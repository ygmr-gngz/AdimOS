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
import { renderMediaOnLambda, getRenderProgress } from '@remotion/lambda/client'
import type { RenderRequest, RenderResponse } from '../types'

const app = express()
app.use(express.json({ limit: '10mb' }))

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

// ── Eşleme tablosu — TEK YER ────────────────────────────────────
// Anahtar: "<video_type>:<format>" veya "<video_type>"
// Değer: src/index.ts'de registerRoot ile kayıtlı composition ID
const COMPOSITION_MAP: Record<string, string> = {
  // Soru çözümü 16:9
  'soru_cozumu:16:9':       'QuizVideo',
  'quiz:16:9':              'QuizVideo',
  // Soru çözümü 9:16 (dikey kısa içerik)
  'soru_cozumu:9:16':       'SplitQuizVerticalDemo',
  'quiz:9:16':              'SplitQuizVerticalDemo',
  'shorts:9:16':            'SplitQuizVerticalDemo',
  'shorts':                 'SplitQuizVerticalDemo',
  'kisa_icerik:9:16':       'SplitQuizVerticalDemo',
  'kisa_icerik':            'SplitQuizVerticalDemo',
  // Motivasyon
  'motivasyon':             'MotivationVideo',
  'motivation':             'MotivationVideo',
  // İnfografik animasyon
  'infografik_animasyon':   'InfographicVideo',
  'infographic':            'InfographicVideo',
  'lesson':                 'InfographicVideo',
  // Konu anlatımı (uzun format)
  'konu_anlatimi':          'LessonVideoDemo',
  'sgs_topic_video':        'LessonVideoDemo',
}

function resolveComposition(videoType: string, format: string): string | null {
  return (
    COMPOSITION_MAP[`${videoType}:${format}`] ??
    COMPOSITION_MAP[videoType] ??
    null
  )
}

// ── Toplam kare tahmini ──────────────────────────────────────────
function estimateTotalFrames(storyboard: any): number {
  if (storyboard?.total_frames)              return storyboard.total_frames
  if (storyboard?.duration_seconds)          return Math.ceil(storyboard.duration_seconds * FPS)
  if (storyboard?.duration_target_minutes)   return Math.ceil(storyboard.duration_target_minutes * 60 * FPS)
  if (Array.isArray(storyboard?.scenes) && storyboard.scenes.length > 0) {
    const totalSec = storyboard.scenes.reduce(
      (acc: number, s: any) => acc + (s.duration_seconds ?? s.duration ?? 5),
      0,
    )
    if (totalSec > 0) return Math.ceil(totalSec * FPS)
  }
  return 3_600 // varsayılan 2 dk
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
  const sb = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
  )
  const path = `videos/${jobId}.mp4`
  const { error } = await sb.storage
    .from('video-outputs')
    .upload(path, buf, { contentType: 'video/mp4', upsert: true })
  if (error) throw new Error(`Supabase upload hatası: ${error.message}`)
  return sb.storage.from('video-outputs').getPublicUrl(path).data.publicUrl
}

// ── Backend callback ─────────────────────────────────────────────
async function _callback(
  jobId:  string,
  status: string,
  extra:  Record<string, unknown> = {},
) {
  const target = `${BACKEND_URL}/video/render-callback`
  await fetch(target, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ job_id: jobId, status, ...extra }),
  }).catch(e => console.warn(`[lambda] callback hatası job=${jobId} → ${target}:`, e.message))
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
  const { renderId, bucketName } = await renderMediaOnLambda({
    region:          LAMBDA_REGION,
    functionName:    LAMBDA_FUNCTION,
    serveUrl:        SERVE_URL,
    composition:     compositionId,
    inputProps:      { storyboard },
    codec:           'h264',
    imageFormat:     'jpeg',
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

// ── POST /render ─────────────────────────────────────────────────
app.post('/render', (req, res) => {
  const { job_id, storyboard } = req.body as RenderRequest

  if (!job_id || !storyboard) {
    return res.status(400).json({ error: 'job_id ve storyboard gerekli' })
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

  const videoType     = storyboard.video_type ?? 'quiz'
  const videoFormat   = storyboard.format      ?? '16:9'
  const compositionId = resolveComposition(videoType, videoFormat)

  if (!compositionId) {
    const validTypes = [...new Set(Object.keys(COMPOSITION_MAP).map(k => k.split(':')[0]))]
    const err =
      `Bilinmeyen iş tipi: "${videoType}" (format: ${videoFormat}). ` +
      `Geçerli tipler: ${validTypes.join(', ')}`
    console.error(`[lambda] ${err}`)
    return res.status(422).json({ error: err })
  }

  if (_isGuardrailHit()) {
    const err =
      `Günlük Lambda maliyet limiti aşıldı ` +
      `($${_dailyCostUsd.toFixed(3)} / $${COST_LIMIT_USD}). ` +
      `DAILY_COST_LIMIT_USD env değişkeni ile artırılabilir.`
    console.error(`[lambda] GUARDRAIL: ${err}`)
    return res.status(429).json({ error: err })
  }

  const totalFrames     = estimateTotalFrames(storyboard)
  const framesPerLambda = Math.max(20, Math.ceil(totalFrames / MAX_CONCURRENT))
  const queuePos        = _renderQueue.length

  console.log(
    `[lambda] kuyruğa alındı: job=${job_id} type=${videoType} format=${videoFormat}` +
    ` composition=${compositionId} frames≈${totalFrames} fpl=${framesPerLambda}` +
    ` maxConcurrent=${MAX_CONCURRENT} sıra=${queuePos}`,
  )

  res.json({
    job_id,
    status:         'started',
    queue_position: queuePos,
    composition_id: compositionId,
  } satisfies RenderResponse & { queue_position: number; composition_id: string })

  _renderQueue.push(async () => {
    const t0           = Date.now()
    const totalElapsed = () => Math.round((Date.now() - t0) / 1_000)

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
      let videoUrl = ''
      if (process.env.SUPABASE_URL && process.env.SUPABASE_SERVICE_ROLE_KEY) {
        const s3Key = _s3KeyFromOutput(result.outputFile, result.renderId, result.bucketName)
        console.log(`[lambda] S3'ten indiriliyor: s3://${result.bucketName}/${s3Key} (outputFile: ${result.outputFile})`)
        const buf = await _s3Download(result.bucketName, s3Key)
        videoUrl  = await _supabaseUpload(buf, job_id)
        console.log(
          `[lambda] Supabase'e yüklendi` +
          ` (${(buf.length / 1024 / 1024).toFixed(1)} MB): ${videoUrl}`,
        )
      }

      await _callback(job_id, 'done', {
        video_url:       videoUrl,
        composition_id:  compositionId,
        render_id:       result.renderId,
        bucket_name:     result.bucketName,
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
  })

  _processQueue()
})

// ── GET /health ───────────────────────────────────────────────────
app.get('/health', (_req, res) => {
  _resetIfNewDay()
  res.json({
    ok:               true,
    service:          'remotion-lambda-bridge-v2',
    port:             PORT,
    lambda_ready:     !!(LAMBDA_FUNCTION && SERVE_URL),
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
// S3'te tamamlanmış ama Supabase'e aktarılamamış render'ı kurtarır.
// Body: { job_id, render_id, bucket_name }
app.post('/rescue', async (req, res) => {
  const { job_id, render_id, bucket_name } = req.body as {
    job_id: string; render_id: string; bucket_name: string
  }
  if (!job_id || !render_id || !bucket_name) {
    return res.status(400).json({ error: 'job_id, render_id ve bucket_name gerekli' })
  }
  console.log(`[lambda] rescue başlıyor: job=${job_id} render=${render_id} bucket=${bucket_name}`)
  try {
    const s3Key = `renders/${render_id}/out.mp4`
    console.log(`[lambda] rescue S3'ten indiriliyor: s3://${bucket_name}/${s3Key}`)
    const buf = await _s3Download(bucket_name, s3Key)
    const videoUrl = await _supabaseUpload(buf, job_id)
    console.log(`[lambda] rescue Supabase'e yüklendi (${(buf.length / 1024 / 1024).toFixed(1)} MB): ${videoUrl}`)
    await _callback(job_id, 'done', {
      video_url:      videoUrl,
      render_id,
      bucket_name,
      rescued:        true,
    })
    res.json({ ok: true, video_url: videoUrl, size_mb: (buf.length / 1024 / 1024).toFixed(1) })
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    console.error(`[lambda] rescue HATA job=${job_id}:`, msg)
    res.status(500).json({ error: msg })
  }
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
app.listen(Number(PORT), '0.0.0.0', () => {
  console.log(`[lambda] hazır → 0.0.0.0:${PORT}`)
  console.log(`[lambda] function=${LAMBDA_FUNCTION || '(eksik)'}`)
  console.log(`[lambda] region=${LAMBDA_REGION}`)
  console.log(`[lambda] serveUrl=${SERVE_URL ? '(ayarlı)' : '(eksik)'}`)
  console.log(`[lambda] backendUrl=${BACKEND_URL}`)
  console.log(`[lambda] maxConcurrent=${MAX_CONCURRENT} costLimit=$${COST_LIMIT_USD}/gün`)
  if (!LAMBDA_FUNCTION || !SERVE_URL) {
    console.warn('[lambda] UYARI: Lambda yapılandırması eksik — /render 503 dönecek')
  }
})
