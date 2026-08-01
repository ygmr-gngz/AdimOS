/**
 * Remotion Lambda Bridge v2 — Railway üzerinde çalışan ince köprü.
 *
 * Akış:
 *   Backend (FastAPI) → POST /render {job_id, storyboard}
 *   → renderMediaOnLambda (AWS Lambda, Chromium yok)
 *   → S3 output → poll → S3'ten indir → Supabase'e yükle
 *   → /video/render-callback ile backend'e bildir
 *
 * Env (Railway Variables):
 *   REMOTION_LAMBDA_FUNCTION_NAME   Lambda fonksiyon adı
 *   REMOTION_SERVE_URL              S3 bundle URL (sites create çıktısı)
 *   REMOTION_AWS_ACCESS_KEY_ID      IAM user key
 *   REMOTION_AWS_SECRET_ACCESS_KEY  IAM user secret
 *   REMOTION_AWS_REGION             → eu-central-1
 *   MAX_CONCURRENT_LAMBDAS          → 8 (kota artınca 200 yap, kod değişmez)
 *   DAILY_COST_LIMIT_USD            → 5.0 (günlük guardrail)
 *   SUPABASE_URL                    Supabase proje URL'i
 *   SUPABASE_SERVICE_ROLE_KEY       Supabase service role key
 *   BACKEND_URL                     FastAPI base URL (callback için)
 */

// ── AWS SDK REMOTION_AWS_* → AWS_* mapping ───────────────────────
// Railway'de REMOTION_AWS_* kullanılıyor; AWS SDK AWS_* okur.
;['ACCESS_KEY_ID', 'SECRET_ACCESS_KEY', 'REGION'].forEach(k => {
  const src = `REMOTION_AWS_${k}`
  const dst = `AWS_${k}`
  if (process.env[src] && !process.env[dst]) {
    process.env[dst] = process.env[src]
  }
})

import express from 'express'
import { createClient } from '@supabase/supabase-js'
import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3'
import { renderMediaOnLambda, getRenderProgress, getCompositionsOnLambda } from '@remotion/lambda/client'
import WebSocket from 'ws'
import type { RenderRequest, RenderResponse } from '../types'

// ── Supabase client (modül düzeyinde bir kere oluştur) ───────────
// Node 20'de native WebSocket yok; ws paketi transport olarak verilir.
// Node 22'de bu satır gereksiz ama zararı yok.
const VIDEO_BUCKET = process.env.SUPABASE_VIDEO_BUCKET || 'video-outputs'

function _makeSupabase() {
  return createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { realtime: { transport: WebSocket as any } },
  )
}
// Lazy init: env değerleri uygulama başladıktan sonra okunur
let _sb: ReturnType<typeof _makeSupabase> | null = null
function _supabase() {
  if (!_sb) _sb = _makeSupabase()
  return _sb
}

// ── Bucket varlık kontrolü + otomatik oluşturma ──────────────────
let _storageReady = false

async function _ensureBucket(): Promise<void> {
  if (!process.env.SUPABASE_URL || !process.env.SUPABASE_SERVICE_ROLE_KEY) {
    console.warn('[lambda] SUPABASE_URL veya SUPABASE_SERVICE_ROLE_KEY eksik — storage kontrolü atlandı')
    return
  }
  const sb = _supabase()
  // Bucket listesini çek
  const { data: buckets, error: listErr } = await sb.storage.listBuckets()
  if (listErr) {
    console.error(`[lambda] Bucket listesi alınamadı: ${listErr.message}`)
    return
  }
  const exists = (buckets ?? []).some(b => b.name === VIDEO_BUCKET)
  if (exists) {
    console.log(`[lambda] storage: bucket "${VIDEO_BUCKET}" mevcut ✓`)
    _storageReady = true
    return
  }
  // Yoksa oluştur (public — frontend getPublicUrl() kullanıyor)
  console.warn(`[lambda] storage: "${VIDEO_BUCKET}" bulunamadı — oluşturuluyor (public)...`)
  const { error: createErr } = await sb.storage.createBucket(VIDEO_BUCKET, {
    public: true,
    allowedMimeTypes: ['video/mp4'],
  })
  if (createErr && !createErr.message.includes('already exists')) {
    console.error(`[lambda] Bucket oluşturulamadı: ${createErr.message}`)
    console.error('[lambda] Supabase Dashboard → Storage → "New bucket" → video-outputs (Public) adıyla elle oluştur')
    return
  }
  console.log(`[lambda] storage: bucket "${VIDEO_BUCKET}" oluşturuldu ✓`)
  _storageReady = true
}

// ── Yüklü remotion sürümünü oku ─────────────────────────────────
// eslint-disable-next-line @typescript-eslint/no-var-requires
const INSTALLED_REMOTION_VERSION: string = (() => {
  try { return (require('remotion/package.json') as { version: string }).version } catch { return 'unknown' }
})()

// ── Lambda fonksiyon adından sürüm çıkar ve karşılaştır ─────────
// Örnek: remotion-render-4-0-488-mem3072mb-... → "4.0.488"
function _parseLambdaVersion(functionName: string): string | null {
  const m = functionName.match(/remotion-render-(\d+)-(\d+)-(\d+)/)
  return m ? `${m[1]}.${m[2]}.${m[3]}` : null
}

function _assertVersionMatch(functionName: string): void {
  const lambdaVer = _parseLambdaVersion(functionName)
  if (!lambdaVer) return  // parse edilemedi, devam et
  if (lambdaVer !== INSTALLED_REMOTION_VERSION) {
    throw new Error(
      `Sürüm uyumsuzluğu: Lambda fonksiyon=${lambdaVer}, ` +
      `@remotion/lambda paketi=${INSTALLED_REMOTION_VERSION}. ` +
      `package.json'daki remotion sürümlerini ${lambdaVer}'e sabitle, npm install çalıştır ve yeniden deploy et.`,
    )
  }
}

const app = express()
app.use(express.json({ limit: '10mb' }))

// REMOTION_PREFLIGHT_STRICT=true  (varsayılan) → altyapı hatası render'ı DURDURUR
// REMOTION_PREFLIGHT_STRICT=false → altyapı hatası loglanır, allowlist ile devam (yalnızca local dev)
const PREFLIGHT_STRICT =
  String(process.env.REMOTION_PREFLIGHT_STRICT ?? 'true').trim().toLowerCase() !== 'false'

function _describeServeUrl(raw: string | undefined) {
  const v = (raw ?? '').trim()
  let host = 'PARSE_FAILED'; let pathHead = '-'
  try { const u = new URL(v); host = u.host; pathHead = u.pathname.split('/').slice(0, 4).join('/') } catch {}
  return {
    present:         v.length > 0,
    length:          v.length,
    starts_https:    v.startsWith('https://'),
    ends_index_html: v.endsWith('/index.html'),
    has_quotes:      /["']/.test(v),
    has_equals:      v.includes('='),
    has_whitespace:  /\s/.test(v),
    has_newline:     /[\r\n]/.test(v),
    host,
    path_head:       pathHead,
  }
}

// Başlangıçta env yapısını logla — değer asla yazılmaz
console.log('[startup] serveUrl', JSON.stringify(_describeServeUrl(process.env.REMOTION_SERVE_URL)))
console.log('[startup] functionName', JSON.stringify({
  present:    Boolean(process.env.REMOTION_LAMBDA_FUNCTION_NAME),
  length:     (process.env.REMOTION_LAMBDA_FUNCTION_NAME ?? '').length,
  has_quotes: /["']/.test(process.env.REMOTION_LAMBDA_FUNCTION_NAME ?? ''),
}))
console.log('[startup] region', JSON.stringify({ value: process.env.AWS_REGION ?? process.env.REMOTION_REGION }))
console.log('[startup] preflight_strict', PREFLIGHT_STRICT)

const PORT            = process.env.PORT || 3001
const LAMBDA_FUNCTION = process.env.REMOTION_LAMBDA_FUNCTION_NAME || ''
const LAMBDA_REGION   = (process.env.AWS_REGION || 'eu-central-1') as Parameters<typeof getRenderProgress>[0]['region']
const SERVE_URL       = process.env.REMOTION_SERVE_URL || ''
const MAX_CONCURRENT  = parseInt(process.env.MAX_CONCURRENT_LAMBDAS || '8',   10)
const COST_LIMIT_USD  = parseFloat(process.env.DAILY_COST_LIMIT_USD  || '5.0'   )
const FPS             = 30
const POLL_MS         = 5_000
const MAX_WAIT_MS     = 25 * 60_000   // 25 dk
const NO_PROGRESS_MS  = 8  * 60_000   // 8 dk hareketsizlik → fail

// BACKEND_URL şemasız gelebilir (örn. "adimos-production.up.railway.app")
// Her durumda https:// ile başlamasını garantile.
function _normalizeBackendUrl(raw: string | undefined): string {
  const url = (raw || 'https://adimos-production.up.railway.app').trim()
  return url.startsWith('http') ? url : `https://${url}`
}
const BACKEND_URL = _normalizeBackendUrl(process.env.BACKEND_URL)

// ── İçerik tipleri — src/generated/content-types.ts (statik TypeScript) ─────────────────
// Docker build context remotion/ olduğu için shared/ JSON'ı runtime require edilemez.
// shared/content-types.json değiştiğinde: npm run sync:content-types && npm run build
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { CONTENT_TYPE_ALIASES, COMPOSITION_MAP } = (() => {
  try {
    return require('../generated/content-types') as {
      CONTENT_TYPE_ALIASES: Record<string, string>
      COMPOSITION_MAP: Record<string, string>
    }
  } catch (e) {
    console.error('[startup] KRİTİK: generated content-types bulunamadı, sync script çalıştırılmamış olabilir')
    console.error('[startup] Çözüm: cd remotion && npm run sync:content-types && npm run build')
    console.error('[startup] Hata:', String(e))
    process.exit(1)
  }
})()

function resolveComposition(rawType: string, format: string): { compositionId: string | null; normalized: string } {
  const lower = (rawType ?? '').trim().toLowerCase()
  const normalized = (CONTENT_TYPE_ALIASES as Record<string, string>)[lower] ?? lower
  const compositionId =
    (COMPOSITION_MAP as Record<string, string>)[`${normalized}:${format}`] ??
    (COMPOSITION_MAP as Record<string, string>)[normalized] ??
    null
  return { compositionId, normalized }
}

// COMPOSITION_MAP'teki tüm geçerli composition ID'leri — preflight allowlist
const ALLOWED_COMPOSITIONS = new Set(Object.values(COMPOSITION_MAP as Record<string, string>))

// ── Toplam kare hesabı — tek kaynak: sahne ölçüm toplamı ──────────────────────
// total_frames girdi olarak geliyorsa yalnızca ±%2 doğrulaması için kullanılır;
// hesabın kaynağı olamaz.
function estimateTotalFrames(storyboard: any, jobId?: string): number {
  const tag = jobId ? ` job=${jobId}` : ''
  const scenes: any[] = Array.isArray(storyboard?.scenes) ? storyboard.scenes : []

  const total = scenes.reduce((acc: number, s: any) => {
    const v = Number(s.duration_seconds)
    return acc + (Number.isFinite(v) ? v : 0)
  }, 0)

  if (!Number.isFinite(total) || total <= 0) {
    throw new Error(
      `duration_validation_failed: geçersiz sahne süreleri` +
      ` (sahne=${scenes.length} toplam=${total})${tag}`,
    )
  }

  const frames = Math.round(total * FPS)
  console.log(
    `[lambda] frames${tag} kaynak=scene_sum_measured` +
    ` sahne=${scenes.length} toplamSn=${total.toFixed(2)} fps=${FPS} değer=${frames}`,
  )

  // total_frames yalnızca doğrulama kapısı — %2 sapma → hata
  if (storyboard?.total_frames != null) {
    const provided = Number(storyboard.total_frames)
    if (Number.isFinite(provided) && provided > 0) {
      const diff = Math.abs(provided - frames) / frames
      if (diff > 0.02) {
        throw new Error(
          `duration_validation_failed: total_frames uyuşmazlığı` +
          ` girdi=${provided} hesaplanan=${frames}` +
          ` sapma=${(diff * 100).toFixed(1)}% (izin=%2)${tag}`,
        )
      }
      console.log(
        `[lambda] frames${tag} total_frames_check girdi=${provided} hesaplanan=${frames} ✓`,
      )
    }
  }

  return frames
}

// ── Günlük maliyet takibi ────────────────────────────────────────
let _dailyCostUsd  = 0
let _dailyCostDate = new Date().toDateString()

function _resetIfNewDay() {
  const today = new Date().toDateString()
  if (today !== _dailyCostDate) { _dailyCostUsd = 0; _dailyCostDate = today }
}

function _addCost(usd: number) {
  _resetIfNewDay()
  _dailyCostUsd += usd
  if (_dailyCostUsd > COST_LIMIT_USD) {
    console.error(
      `[lambda] GUARDRAIL Günlük maliyet $${_dailyCostUsd.toFixed(3)} — limit $${COST_LIMIT_USD}`,
    )
  }
}

function _isGuardrailHit(): boolean {
  _resetIfNewDay()
  return _dailyCostUsd >= COST_LIMIT_USD
}

// ── S3 key çözümleyici ───────────────────────────────────────────
// getRenderProgress.outputFile şu formatlarda gelebilir:
//   (a) s3://bucket/renders/xxx/out.mp4
//   (b) https://s3.eu-central-1.amazonaws.com/bucket/renders/xxx/out.mp4  (path-style)
//   (c) https://bucket.s3.eu-central-1.amazonaws.com/renders/xxx/out.mp4  (virtual-hosted)
// Her durumda "renders/xxx/out.mp4" döndür.
function _s3KeyFromOutput(outputFile: string, renderId: string, bucketName: string): string {
  try {
    if (outputFile.startsWith('s3://')) {
      // s3://bucket/renders/xxx/out.mp4 → renders/xxx/out.mp4
      return outputFile.split('/').slice(3).join('/')
    }
    if (outputFile.startsWith('http')) {
      const url = new URL(outputFile)
      const parts = url.pathname.split('/').filter(Boolean)
      // Path-style: hostname = s3.*.amazonaws.com, ilk part = bucket adı
      // Virtual-hosted: hostname = bucket.s3.*.amazonaws.com, tüm parts = key
      const isPathStyle = !url.hostname.startsWith(bucketName)
      const keyParts = isPathStyle ? parts.slice(1) : parts
      if (keyParts.length > 0) return keyParts.join('/')
    }
  } catch { /* parse hatası → fallback */ }
  // Remotion Lambda her zaman bu path'i kullanır
  return `renders/${renderId}/out.mp4`
}

// ── Render kuyruğu (maks 1 eşzamanlı) ───────────────────────────
let _renderRunning = false
const _renderQueue: Array<() => Promise<void>> = []

async function _processQueue() {
  if (_renderRunning || _renderQueue.length === 0) return
  _renderRunning = true
  const task = _renderQueue.shift()!
  try { await task() } finally {
    _renderRunning = false
    _processQueue()
  }
}

// ── S3 → Buffer ──────────────────────────────────────────────────
async function _s3Download(bucket: string, key: string): Promise<Buffer> {
  const s3 = new S3Client({ region: LAMBDA_REGION })
  const { Body } = await s3.send(new GetObjectCommand({ Bucket: bucket, Key: key }))
  if (!Body) throw new Error(`S3 boş yanıt: s3://${bucket}/${key}`)
  const chunks: Buffer[] = []
  for await (const chunk of Body as NodeJS.ReadableStream) {
    chunks.push(Buffer.from(chunk))
  }
  return Buffer.concat(chunks)
}

// ── Buffer → Supabase Storage ─────────────────────────────────────
async function _supabaseUpload(buf: Buffer, jobId: string): Promise<string> {
  const sb      = _supabase()
  const stoPath = `videos/${jobId}.mp4`
  const { error } = await sb.storage
    .from(VIDEO_BUCKET)
    .upload(stoPath, buf, { contentType: 'video/mp4', upsert: true })
  if (error) throw new Error(`Supabase upload hatası: ${error.message}`)
  return sb.storage.from(VIDEO_BUCKET).getPublicUrl(stoPath).data.publicUrl
}

// ── Backend callback ─────────────────────────────────────────────
// Progress (status='rendering') loglanır ama backend'e gönderilmez:
// backend handler'ı sadece 'done'/'failed' bekler; 'rendering' gönderilirse
// else→failed dalına girer ve işi erken bitirir.
async function _callback(
  jobId:  string,
  status: string,
  extra:  Record<string, unknown> = {},
) {
  if (status === 'rendering') {
    console.log(`[lambda] progress job=${jobId}`, JSON.stringify(extra))
    return
  }

  const target = `${BACKEND_URL}/api/v1/video/render-callback`
  const body   = JSON.stringify({ job_id: jobId, status, ...extra })

  // 3 deneme, exponential backoff: 2s → 4s → 8s
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const res = await fetch(target, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body,
      })
      if (res.ok) {
        console.log(`[lambda] callback OK job=${jobId} status=${status} HTTP ${res.status}`)
        return
      }
      console.warn(
        `[lambda] callback HTTP ${res.status} job=${jobId} status=${status} girişim=${attempt}`,
      )
    } catch (e) {
      console.warn(
        `[lambda] callback ağ hatası job=${jobId} girişim=${attempt}:`,
        (e as Error).message,
      )
    }
    if (attempt < 3) {
      await new Promise(r => setTimeout(r, 2_000 * Math.pow(2, attempt - 1)))
    }
  }
  console.error(
    `[lambda] callback 3 girişimde başarısız — job=${jobId} status=${status} target=${target}`,
  )
}

// ── Render çekirdeği ─────────────────────────────────────────────
interface RenderResult {
  renderId:   string
  bucketName: string
  outputFile: string
  costUsd:    number
}

async function _doRender(
  jobId:           string,
  storyboard:      any,
  compositionId:   string,
  framesPerLambda: number,
  attempt = 1,
): Promise<RenderResult> {
  // Sürüm uyumsuzluğunu anında tespit et — 15 dk bekleme yerine hemen fail
  _assertVersionMatch(LAMBDA_FUNCTION)

  // ── Yerel allowlist kontrolü (altyapıdan bağımsız, her zaman çalışır) ────────
  if (!ALLOWED_COMPOSITIONS.has(compositionId)) {
    throw new Error(`İzin verilmeyen composition ID: "${compositionId}"`)
  }

  // inputProps: bir kez oluştur, preflight ve render aynı nesneyi alır
  const rawInputProps: unknown = { storyboard }
  const inputProps: Record<string, unknown> =
    rawInputProps === null || rawInputProps === undefined || Array.isArray(rawInputProps)
      ? {}
      : (rawInputProps as Record<string, unknown>)
  console.log(`[preflight] inputProps keys=${Object.keys(inputProps).join(',')}`)

  // ── Lambda preflight — composition yeni bundle'da kayıtlı mı? ────────────────
  // Altyapı hatası (ağ, AWS iç hata, response parse) ile composition eksikliğini ayır.
  try {
    const rawResult: unknown = await getCompositionsOnLambda({
      region:                LAMBDA_REGION,
      functionName:          LAMBDA_FUNCTION,
      serveUrl:              SERVE_URL,
      inputProps,
      timeoutInMilliseconds: 30_000,
    })

    // Dönüş tipini logla — hassas veri yok
    console.log(`[preflight] response type=${Array.isArray(rawResult) ? 'array' : typeof rawResult}`)

    // Remotion 4.x doğrudan dizi döndürür; wrapped obje formatını da destekle
    let allComps: Array<{ id: string }>
    if (Array.isArray(rawResult)) {
      allComps = rawResult as Array<{ id: string }>
    } else if (
      rawResult !== null &&
      typeof rawResult === 'object' &&
      Array.isArray((rawResult as Record<string, unknown>).compositions)
    ) {
      allComps = (rawResult as Record<string, unknown>).compositions as Array<{ id: string }>
      console.log('[preflight] wrapped response (.compositions) şekli')
    } else {
      if (rawResult !== null && typeof rawResult === 'object') {
        console.log(`[preflight] response keys=${Object.keys(rawResult as object).join(',')}`)
      }
      throw new Error(
        `getCompositionsOnLambda beklenen composition dizisini döndürmedi (type=${typeof rawResult})`,
      )
    }

    const ids = allComps
      .filter((item): item is { id: string } =>
        Boolean(item) && typeof (item as Record<string, unknown>).id === 'string',
      )
      .map(item => item.id)

    if (!ids.includes(compositionId)) {
      throw new Error(
        `Composition bulunamadı: "${compositionId}". ` +
        `Bundle'da mevcut: [${ids.join(', ')}]. ` +
        `Çözüm: npm run deploy:site → Railway REMOTION_SERVE_URL güncelle`,
      )
    }
    console.log(`[preflight] composition doğrulandı: "${compositionId}" fallback_used=false render_started=true`)

  } catch (e) {
    const err = e instanceof Error ? e : new Error(String(e))
    console.error(`[preflight] HATA: ${err.message}`)
    console.error(`[preflight] stack: ${err.stack ?? 'stack yok'}`)

    // Composition gerçekten eksik veya API beklenen format dışı dönüş yaptı → her zaman fail
    if (
      err.message.includes('Composition bulunamadı') ||
      err.message.includes('döndürmedi')
    ) {
      throw err
    }

    // Altyapı hatası (ağ, AWS iç hata, Lambda response parse hatası)
    if (PREFLIGHT_STRICT) {
      console.error('[preflight] strict=true remote_check=failed fallback_used=false render_started=false reason=' + err.message)
      throw new Error(`preflight_failed: ${err.message}`)
    }
    // strict=false: allowlist ile devam — sadece dev/test ortamı
    console.warn(
      `[preflight] strict=false remote_check=failed fallback_used=true render_started=true composition=${compositionId}`,
    )
  }

  const { renderId, bucketName } = await renderMediaOnLambda({
    region:          LAMBDA_REGION,
    functionName:    LAMBDA_FUNCTION,
    serveUrl:        SERVE_URL,
    composition:     compositionId,
    inputProps,
    codec:           'h264',
    imageFormat:     'jpeg',
    pixelFormat:     'yuv420p',
    maxRetries:      1,
    framesPerLambda,
    privacy:         'private',
  })

  console.log(
    `[lambda] render başlatıldı: job=${jobId} composition=${compositionId}` +
    ` renderId=${renderId} fpl=${framesPerLambda} girişim=${attempt}`,
  )

  const pollStart               = Date.now()
  let outputFile: string | null = null
  let costUsd                   = 0
  let lastProgressTime          = Date.now()
  let lastPct                   = -1
  let lastCallbackPct           = -1
  const elapsed = () => Math.round((Date.now() - pollStart) / 1_000)

  while (Date.now() - pollStart < MAX_WAIT_MS) {
    await new Promise(r => setTimeout(r, POLL_MS))

    const prog = await getRenderProgress({
      renderId,
      bucketName,
      functionName: LAMBDA_FUNCTION,
      region:       LAMBDA_REGION,
    })

    const pct = Math.round(prog.overallProgress * 100)

    if (pct !== lastPct) {
      lastProgressTime = Date.now()
      lastPct = pct
    } else if (Date.now() - lastProgressTime > NO_PROGRESS_MS) {
      throw new Error(`Render ${NO_PROGRESS_MS / 60_000} dakikadır ilerlemedi — iptal edildi`)
    }

    // Her 10%'de bir log + backend progress callback
    if (pct >= lastCallbackPct + 10) {
      lastCallbackPct = Math.floor(pct / 10) * 10
      console.log(
        `[lambda] job=${jobId} composition=${compositionId}` +
        ` ilerleme=${lastCallbackPct}% (${elapsed()}s)`,
      )
      _callback(jobId, 'rendering', {
        progress_pct:   lastCallbackPct,
        composition_id: compositionId,
        render_id:      renderId,
      })
    }

    const costs = (prog as any).costs
    if (costs?.accruedSoFar?.currency === 'USD') {
      costUsd = costs.accruedSoFar.value
    }

    if (prog.done) {
      outputFile = (prog as any).outputFile ?? null
      break
    }

    if (prog.fatalErrorEncountered) {
      const msgs = ((prog as any).errors ?? [])
        .map((e: any) => e.message as string)
        .join('; ')
      throw new Error(msgs || 'Lambda render — bilinmeyen hata')
    }
  }

  if (!outputFile) {
    throw new Error(`Render ${MAX_WAIT_MS / 60_000} dakikada tamamlanmadı`)
  }

  return { renderId, bucketName, outputFile, costUsd }
}

// ── Tür bazında props doğrulama (per-type builders) ──────────────

function _sceneSummary(storyboard: any, compositionId: string, job_id: string, prefix: string) {
  const scenes: any[] = storyboard.scenes ?? []
  const totalSec = scenes.reduce((sum: number, s: any) => {
    const d = Number(s.duration_seconds)
    return sum + (isFinite(d) ? d : 0)
  }, 0)
  const audioReady   = scenes.filter((s: any) => s.tts_url).length
  const ffprobeCount = scenes.filter((s: any) => s.duration_source === 'ffprobe').length
  const captionCount = scenes.filter((s: any) => Array.isArray(s.captions) && s.captions.length > 0).length
  const badDurations = scenes.filter((s: any) => {
    const d = Number(s.duration_seconds)
    return !isFinite(d) || d <= 0
  }).length

  console.log(
    `[${prefix}] job=${job_id} composition=${compositionId}` +
    ` scenes=${scenes.length} measured_total_sec=${totalSec.toFixed(2)}` +
    ` audio_ready=${audioReady}/${scenes.length}` +
    ` duration_source=ffprobe:${ffprobeCount}` +
    ` captions=${captionCount}/${scenes.length}`,
  )
  if (badDurations > 0) {
    console.error(`[${prefix}] ${badDurations}/${scenes.length} sahnede duration_seconds geçersiz`)
  }
  return { scenes, totalSec }
}

function _toleranceCheck(storyboard: any, compositionId: string, totalSec: number, prefix: string): { error: string; message: string } | null {
  const requested = Number(storyboard.requested_duration_seconds)
  if (!requested || totalSec <= 0) return null
  const tolerance = Number(storyboard.duration_tolerance_seconds ?? 8)
  const lo = requested - tolerance
  const hi = requested + tolerance
  if (totalSec < lo || totalSec > hi) {
    const msg = `${compositionId}: istek=${requested}s ±${tolerance}s gerçek=${totalSec.toFixed(2)}s izin=${lo.toFixed(0)}–${hi.toFixed(0)}s`
    console.error(`[${prefix}] HARD FAIL duration_validation_failed: ${msg}`)
    return { error: 'duration_validation_failed', message: msg }
  }
  return null
}

function _validateProps(
  storyboard: any, compositionId: string, normalizedType: string, job_id: string,
): { error: string; message: string } | null {

  switch (compositionId) {
    case 'LessonVideo': {
      const { scenes, totalSec } = _sceneSummary(storyboard, compositionId, job_id, 'lesson-props')
      if (scenes.length > 0 && scenes.length < 8) {
        const msg = `LessonVideo: ${scenes.length} sahne — minimum 8 sahne gerekli`
        console.error(`[lesson-props] HARD FAIL insufficient_scene_count: ${msg}`)
        return { error: 'insufficient_scene_count', message: msg }
      }
      return _toleranceCheck(storyboard, compositionId, totalSec, 'lesson-props')
    }
    case 'QuizVideo':
    case 'SplitQuizVerticalDemo': {
      const { totalSec } = _sceneSummary(storyboard, compositionId, job_id, 'quizboard-props')
      return _toleranceCheck(storyboard, compositionId, totalSec, 'quizboard-props')
    }
    case 'EducationalReel':
    case 'EducationalReel120': {
      const { scenes, totalSec } = _sceneSummary(storyboard, compositionId, job_id, 'reel-props')
      if (scenes.length > 0 && totalSec > 0) {
        const tolErr = _toleranceCheck(storyboard, compositionId, totalSec, 'reel-props')
        if (tolErr) return tolErr
      }
      return null
    }
    case 'MotivationVideo': {
      const { totalSec } = _sceneSummary(storyboard, compositionId, job_id, 'motivation-props')
      return _toleranceCheck(storyboard, compositionId, totalSec, 'motivation-props')
    }
    case 'InfographicVideo': {
      const { totalSec } = _sceneSummary(storyboard, compositionId, job_id, 'infographic-props')
      return _toleranceCheck(storyboard, compositionId, totalSec, 'infographic-props')
    }
    case 'QuizBoardVideo': {
      const { totalSec } = _sceneSummary(storyboard, compositionId, job_id, 'quizboard-props')
      return _toleranceCheck(storyboard, compositionId, totalSec, 'quizboard-props')
    }
    default: {
      _sceneSummary(storyboard, compositionId, job_id, 'props')
      return null
    }
  }
}

// ── İşlemde olan job'ların in-memory kümesi (process restart ile sıfırlanır) ──
// DB atomik geçişi ile birlikte iki katman koruma sağlar:
// 1. Aynı process içinde aynı job_id iki kez gelmişse anında 409 dön.
// 2. Farklı process / restart → DB WHERE status='queued' katmanı devreye girer.
const _activeJobIds = new Set<string>()

// ── POST /render ─────────────────────────────────────────────────
app.post('/render', (req, res) => {
  const { job_id, storyboard } = req.body as RenderRequest

  if (!job_id || !storyboard) {
    return res.status(400).json({ error: 'job_id ve storyboard gerekli' })
  }

  // İn-memory çift-render koruması
  if (_activeJobIds.has(job_id)) {
    console.warn(`[lambda] duplicate_render_blocked job=${job_id} — zaten işlemde`)
    return res.status(409).json({ error: 'job_already_active', job_id })
  }

  if (!LAMBDA_FUNCTION || !SERVE_URL) {
    console.error('[lambda] REMOTION_LAMBDA_FUNCTION_NAME veya REMOTION_SERVE_URL eksik')
    return res.status(503).json({
      error:   'Lambda yapılandırılmamış',
      missing: {
        REMOTION_LAMBDA_FUNCTION_NAME: !LAMBDA_FUNCTION,
        REMOTION_SERVE_URL:            !SERVE_URL,
      },
    })
  }

  const rawType       = String(storyboard.video_type ?? 'quiz')
  const videoFormat   = storyboard.format ?? '16:9'
  const { compositionId, normalized: normalizedType } = resolveComposition(rawType, videoFormat)

  if (rawType !== normalizedType) {
    console.warn(`[lambda] type_normalized raw=${rawType} → ${normalizedType}`)
  }
  console.log(`[lambda] type raw=${rawType} normalized=${normalizedType} composition=${compositionId ?? 'null'}`)

  if (!compositionId) {
    const validTypes = [...new Set(Object.keys(COMPOSITION_MAP as Record<string, string>).map(k => k.split(':')[0]))]
    const err =
      `Bilinmeyen iş tipi: "${rawType}" (format: ${videoFormat}). ` +
      `Geçerli tipler: ${validTypes.sort().join(', ')}`
    console.error(`[lambda] ${err}`)
    return res.status(422).json({ error: 'unknown_content_type', message: err })
  }

  if (_isGuardrailHit()) {
    const err =
      `Günlük Lambda maliyet limiti aşıldı ` +
      `($${_dailyCostUsd.toFixed(3)} / $${COST_LIMIT_USD}). ` +
      `DAILY_COST_LIMIT_USD env değişkeni ile artırılabilir.`
    console.error(`[lambda] GUARDRAIL: ${err}`)
    return res.status(429).json({ error: err })
  }

  // ── Tür bazında props doğrulaması (hard fail) ─────────────────────────────
  const _propsErr = _validateProps(storyboard, compositionId, normalizedType, job_id)
  if (_propsErr) {
    return res.status(422).json(_propsErr)
  }

  let totalFrames: number
  try {
    totalFrames = estimateTotalFrames(storyboard, job_id)
  } catch (durErr: any) {
    console.error(`[lambda] duration_validation_failed job=${job_id}: ${durErr.message}`)
    return res.status(422).json({ error: 'duration_validation_failed', message: durErr.message })
  }

  const framesPerLambda = Math.max(20, Math.ceil(totalFrames / MAX_CONCURRENT))
  const queuePos        = _renderQueue.length

  console.log(
    `[lambda] kuyruğa alındı: job=${job_id} type=${normalizedType} format=${videoFormat}` +
    ` composition=${compositionId} frames≈${totalFrames} fpl=${framesPerLambda}` +
    ` maxConcurrent=${MAX_CONCURRENT} sıra=${queuePos}`,
  )

  res.json({
    job_id,
    status:         'started',
    queue_position: queuePos,
    composition_id: compositionId,
  } satisfies RenderResponse & { queue_position: number; composition_id: string })

  _activeJobIds.add(job_id)

  _renderQueue.push(async () => {
    const t0           = Date.now()
    const totalElapsed = () => Math.round((Date.now() - t0) / 1_000)

    try {
    // ── Atomik durum geçişi: rendering — çift-render koruması ──────────────
    // WHERE status='queued' önkoşulu: eğer başka worker zaten aldıysa
    // veya backend erken iptal ettiyse RETURNING id boş gelir → çıkış.
    try {
      const sb = _supabase()
      const { data: claimed } = await sb
        .from('video_jobs')
        .update({ status: 'rendering', updated_at: new Date().toISOString() })
        .eq('id', job_id)
        .eq('status', 'queued')
        .select('id')
      if (!claimed || claimed.length === 0) {
        console.warn(
          `[lambda] atomik_gecis_basarisiz job=${job_id} ` +
          `— status='queued' değil, başka worker almış olabilir; render atlanıyor`,
        )
        return
      }
      console.log(`[lambda] atomik_gecis_ok job=${job_id} → rendering`)
    } catch (sbErr: any) {
      // Supabase erişilemez durumdaysa render devam etsin ama uyar
      console.warn(
        `[lambda] atomik_gecis_hata job=${job_id}: ${sbErr.message} ` +
        `— Supabase kontrol atlandı, render devam edecek`,
      )
    }

    try {
      const result = await _doRender(
        job_id, storyboard, compositionId, framesPerLambda,
      ).catch(async err => {
        // Rate Exceeded → framesPerLambda 2× artır, bir kez yeniden dene
        if (/rate.*exceeded|too many.*request|throttl/i.test(String(err))) {
          const retryFpl = Math.ceil(framesPerLambda * 2)
          console.warn(
            `[lambda] Rate Exceeded job=${job_id}` +
            ` — framesPerLambda ${framesPerLambda}→${retryFpl} yeniden deneniyor`,
          )
          await _callback(job_id, 'rendering', {
            message:        'AWS kapasitesi aşıldı, yeniden deneniyor...',
            composition_id: compositionId,
          })
          return _doRender(job_id, storyboard, compositionId, retryFpl, 2)
        }
        throw err
      })

      _addCost(result.costUsd)
      console.log(
        `[lambda] render tamam (${totalElapsed()}s):` +
        ` composition=${compositionId}` +
        ` maliyet=$${result.costUsd.toFixed(4)}` +
        ` günlük=$${_dailyCostUsd.toFixed(4)}`,
      )

      // S3 → Supabase
      const s3Key        = _s3KeyFromOutput(result.outputFile, result.renderId, result.bucketName)
      const s3BackupPath = `s3://${result.bucketName}/${s3Key}`
      let videoUrl       = ''

      if (process.env.SUPABASE_URL && process.env.SUPABASE_SERVICE_ROLE_KEY) {
        console.log(`[lambda] S3'ten indiriliyor: ${s3BackupPath}`)
        const buf = await _s3Download(result.bucketName, s3Key)

        try {
          videoUrl = await _supabaseUpload(buf, job_id)
          console.log(`[lambda] Supabase'e yüklendi (${(buf.length / 1024 / 1024).toFixed(1)} MB): ${videoUrl}`)
        } catch (uploadErr) {
          // Upload başarısız — S3 yolu callback'e yazılır; rescue her zaman mümkün
          const uploadMsg = uploadErr instanceof Error ? uploadErr.message : String(uploadErr)
          console.error(`[lambda] Supabase upload hatası job=${job_id}: ${uploadMsg}`)
          console.error(`[lambda] Video S3'te güvende: ${s3BackupPath}`)
          await _callback(job_id, 'failed', {
            error:          `Supabase upload başarısız: ${uploadMsg}`,
            s3_backup_path: s3BackupPath,
            render_id:      result.renderId,
            bucket_name:    result.bucketName,
            composition_id: compositionId,
            elapsed_seconds: totalElapsed(),
          })
          return
        }
      }

      await _callback(job_id, 'done', {
        video_url:       videoUrl,
        composition_id:  compositionId,
        render_id:       result.renderId,
        bucket_name:     result.bucketName,
        s3_backup_path:  s3BackupPath,
        cost_lambda_usd: result.costUsd,
        elapsed_seconds: totalElapsed(),
      })
      console.log(`[lambda] job=${job_id} tamamlandı — toplam ${totalElapsed()}s`)

    } catch (err) {
      const msg      = err instanceof Error ? err.message : String(err)
      const friendly =
        msg.includes('ilerlemedi')    ? `Lambda 8 dk yanıt vermedi — iptal` :
        msg.includes('tamamlanmadı') ? `25 dk içinde render tamamlanamadı` :
        msg.includes('upload hatası') ? msg :
                                        `Render hatası: ${msg}`
      console.error(`[lambda] HATA job=${job_id} (${totalElapsed()}s): ${msg}`)
      await _callback(job_id, 'failed', {
        error:          `${friendly} (${totalElapsed()}s sonra)`,
        composition_id: compositionId,
      })
    }

    } finally {
      // Her durumda (başarı, hata, atomik_gecis_basarisiz) job kümesinden çıkar
      _activeJobIds.delete(job_id)
    }
  })

  _processQueue()
})

// ── SERVE_URL'den Lambda S3 bucket adını çıkar ───────────────────
function _lambdaS3Bucket(): string {
  if (!SERVE_URL) return '(eksik)'
  try {
    const u = new URL(SERVE_URL)
    // virtual-hosted: remotionlambda-xxx.s3.region.amazonaws.com
    if (u.hostname.startsWith('remotionlambda')) return u.hostname.split('.')[0]
    // path-style: s3.region.amazonaws.com/remotionlambda-xxx/...
    return u.pathname.split('/').filter(Boolean)[0] || '(parse-hatası)'
  } catch { return '(parse-hatası)' }
}

// ── GET /health ───────────────────────────────────────────────────
app.get('/health', (_req, res) => {
  _resetIfNewDay()
  const lambdaReady   = !!(LAMBDA_FUNCTION && SERVE_URL)
  const allReady      = lambdaReady && _storageReady
  res.json({
    ok:               allReady,
    service:          'remotion-lambda-bridge-v2',
    port:             PORT,
    lambda_ready:     lambdaReady,
    storage_ready:    _storageReady,
    storage_bucket:   VIDEO_BUCKET,
    lambda_s3_bucket: _lambdaS3Bucket(),
    lambda_function:  LAMBDA_FUNCTION  || '(eksik)',
    lambda_region:    LAMBDA_REGION,
    serve_url:        SERVE_URL ? '(ayarlı)' : '(eksik)',
    max_concurrent:   MAX_CONCURRENT,
    render_running:   _renderRunning,
    queue_length:     _renderQueue.length,
    daily_cost_usd:   _dailyCostUsd,
    daily_cost_limit: COST_LIMIT_USD,
    guardrail_hit:    _isGuardrailHit(),
    compositions:     [...new Set(Object.values(COMPOSITION_MAP))],
  })
})

// ── GET /compositions ─────────────────────────────────────────────
app.get('/compositions', (_req, res) => {
  res.json({ mapping: COMPOSITION_MAP })
})

// ── POST /rescue ──────────────────────────────────────────────────
// S3'te tamamlanmış ama Supabase'e aktarılamamış render'ları kurtarır.
// Tek iş: { job_id, render_id, bucket_name }
// Toplu:  [{ job_id, render_id, bucket_name }, ...]
interface RescueItem { job_id: string; render_id: string; bucket_name: string }

async function _rescueOne(item: RescueItem): Promise<{ ok: boolean; job_id: string; video_url?: string; size_mb?: string; error?: string }> {
  const { job_id, render_id, bucket_name } = item
  console.log(`[lambda] rescue: job=${job_id} render=${render_id} bucket=${bucket_name}`)
  try {
    const s3Key    = `renders/${render_id}/out.mp4`
    const buf      = await _s3Download(bucket_name, s3Key)
    const videoUrl = await _supabaseUpload(buf, job_id)
    console.log(`[lambda] rescue tamam: job=${job_id} (${(buf.length / 1024 / 1024).toFixed(1)} MB) → ${videoUrl}`)
    await _callback(job_id, 'done', { video_url: videoUrl, render_id, bucket_name, rescued: true })
    return { ok: true, job_id, video_url: videoUrl, size_mb: (buf.length / 1024 / 1024).toFixed(1) }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    console.error(`[lambda] rescue HATA job=${job_id}:`, msg)
    return { ok: false, job_id, error: msg }
  }
}

app.post('/rescue', async (req, res) => {
  const items: RescueItem[] = Array.isArray(req.body) ? req.body : [req.body]
  const invalid = items.find(i => !i.job_id || !i.render_id || !i.bucket_name)
  if (invalid) {
    return res.status(400).json({ error: 'Her iş için job_id, render_id ve bucket_name gerekli' })
  }
  // Sıralı çalıştır — birden fazla işte paralel S3 indirme Supabase'i zorlayabilir
  const results = []
  for (const item of items) results.push(await _rescueOne(item))
  const allOk = results.every(r => r.ok)
  res.status(allOk ? 200 : 207).json(results.length === 1 ? results[0] : results)
})

// ── Graceful shutdown ─────────────────────────────────────────────
let _shuttingDown = false
function _shutdown(sig: string) {
  if (_shuttingDown) return
  _shuttingDown = true
  console.log(`[lambda] ${sig} — queue=${_renderQueue.length} active=${_renderRunning}`)
  setTimeout(() => { console.log('[lambda] shutdown ok'); process.exit(0) }, 8_000)
}
process.on('SIGTERM', () => _shutdown('SIGTERM'))
process.on('SIGINT',  () => _shutdown('SIGINT'))
process.on('uncaughtException',  err    => { console.error('[lambda] CRASH:', err); process.exit(1) })
process.on('unhandledRejection', reason => console.error('[lambda] unhandledRejection:', reason))

// ── Başlat ────────────────────────────────────────────────────────
console.log(`[lambda] Lambda Bridge v2 başlıyor PORT=${PORT}`)
// Bucket varlığını başlangıçta kontrol et / oluştur
_ensureBucket().catch(e => console.error('[lambda] _ensureBucket hatası:', e))

app.listen(Number(PORT), '0.0.0.0', () => {
  console.log(`[lambda] hazır → 0.0.0.0:${PORT}`)
  console.log(`[lambda] function=${LAMBDA_FUNCTION || '(eksik)'}`)
  console.log(`[lambda] region=${LAMBDA_REGION}`)
  console.log(`[lambda] serveUrl=${SERVE_URL ? '(ayarlı)' : '(eksik)'}`)
  console.log(`[lambda] backendUrl=${BACKEND_URL}`)
  console.log(`[lambda] remotion paketi=${INSTALLED_REMOTION_VERSION}`)
  const lambdaVer = _parseLambdaVersion(LAMBDA_FUNCTION)
  if (lambdaVer && lambdaVer !== INSTALLED_REMOTION_VERSION) {
    console.error(`[lambda] UYARI: Sürüm uyumsuzluğu — Lambda=${lambdaVer} paket=${INSTALLED_REMOTION_VERSION} — render'lar anında başarısız olacak`)
  } else if (lambdaVer) {
    console.log(`[lambda] sürüm eşleşiyor: ${lambdaVer} ✓`)
  }
  console.log(`[lambda] maxConcurrent=${MAX_CONCURRENT} costLimit=$${COST_LIMIT_USD}/gün`)
  if (!LAMBDA_FUNCTION || !SERVE_URL) {
    console.warn('[lambda] UYARI: Lambda yapılandırması eksik — /render 503 dönecek')
  }
})
