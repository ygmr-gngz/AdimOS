/**
 * Remotion Lambda Bridge — Railway'de çalışan ince köprü servisi.
 *
 * ÖNCEKİ DURUM: renderMedia() → Chromium → 8 GB RAM → OOM crash
 * YENİ DURUM:   renderMediaOnLambda() → AWS Lambda → 0 Chromium → <256 MB RAM
 *
 * Backend Python ile API yüzeyi AYNI → backend'de sıfır değişiklik:
 *   POST /render { job_id, storyboard } → hemen {status:'started'} döner
 *   Lambda render tamamlanınca → Supabase Storage → /video/render-callback
 */
import express from 'express'
import { createClient } from '@supabase/supabase-js'
import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3'
import { renderMediaOnLambda, getRenderProgress } from '@remotion/lambda/client'
import type { RenderRequest, RenderResponse } from '../types'

const app = express()
app.use(express.json({ limit: '10mb' }))

const PORT             = process.env.PORT || 3001
const LAMBDA_FUNCTION  = process.env.REMOTION_LAMBDA_FUNCTION_NAME || ''
const LAMBDA_REGION    = process.env.REMOTION_LAMBDA_REGION || 'eu-central-1'
const SERVE_URL        = process.env.REMOTION_SERVE_URL || ''   // S3 bundle URL

// ── Render kuyruğu (max 1 eşzamanlı — Lambda'da CPU sınırı yok ama
//    queue tutulur: ani patlamada backend sıraya alır, kayıp olmaz) ──
let _renderRunning = false
const _renderQueue: Array<() => Promise<void>> = []

async function _processQueue() {
  if (_renderRunning || _renderQueue.length === 0) return
  _renderRunning = true
  const task = _renderQueue.shift()!
  try {
    await task()
  } finally {
    _renderRunning = false
    _processQueue()
  }
}

// ── S3'ten buffer olarak indir ────────────────────────────────
async function _s3Download(bucket: string, key: string): Promise<Buffer> {
  const s3 = new S3Client({ region: LAMBDA_REGION })
  const resp = await s3.send(new GetObjectCommand({ Bucket: bucket, Key: key }))
  const chunks: Buffer[] = []
  for await (const chunk of resp.Body as NodeJS.ReadableStream) {
    chunks.push(Buffer.from(chunk))
  }
  return Buffer.concat(chunks)
}

// ── Supabase video-outputs bucket'a yükle ────────────────────
async function _supabaseUpload(buf: Buffer, jobId: string): Promise<string> {
  const sb = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
  )
  const path = `videos/${jobId}.mp4`
  await sb.storage.from('video-outputs').upload(path, buf, {
    contentType: 'video/mp4',
    upsert: true,
  })
  const { data } = sb.storage.from('video-outputs').getPublicUrl(path)
  return data.publicUrl
}

// ── Backend callback ─────────────────────────────────────────
async function _callback(jobId: string, status: string, extra: Record<string, unknown> = {}) {
  const backendUrl = process.env.BACKEND_URL
  if (!backendUrl) return
  await fetch(`${backendUrl}/video/render-callback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_id: jobId, status, ...extra }),
  }).catch(e => console.warn(`[lambda] callback hatası job=${jobId}:`, e.message))
}

// ── Render endpoint ───────────────────────────────────────────
app.post('/render', (req, res) => {
  const { job_id, storyboard } = req.body as RenderRequest

  if (!job_id || !storyboard) {
    return res.status(400).json({ error: 'job_id ve storyboard gerekli' })
  }

  if (!LAMBDA_FUNCTION || !SERVE_URL) {
    console.error('[lambda] REMOTION_LAMBDA_FUNCTION_NAME veya REMOTION_SERVE_URL eksik')
    return res.status(503).json({
      error: 'Lambda yapılandırılmamış',
      missing: {
        REMOTION_LAMBDA_FUNCTION_NAME: !LAMBDA_FUNCTION,
        REMOTION_SERVE_URL: !SERVE_URL,
      },
    })
  }

  const queuePos = _renderQueue.length
  console.log(`[lambda] kuyruğa alındı: job=${job_id} tip=${storyboard.video_type} sıra=${queuePos}`)
  res.json({ job_id, status: 'started', queue_position: queuePos } as RenderResponse & { queue_position: number })

  _renderQueue.push(async () => {
    const t0 = Date.now()
    const elapsed = () => Math.round((Date.now() - t0) / 1000)

    console.log(`[lambda] render başlıyor: job=${job_id} tip=${storyboard.video_type}`)

    const compositionId =
      storyboard.video_type === 'motivation'    ? 'MotivationVideo' :
      storyboard.video_type === 'lesson'        ? 'InfographicVideo' :
      storyboard.video_type === 'konu_anlatimi' ? 'QuizVideo' :
      'QuizVideo'

    try {
      // ── 1. Lambda render başlat ─────────────────────────────
      console.log(`[lambda] renderMediaOnLambda başlıyor: ${compositionId}`)
      const { renderId, bucketName } = await renderMediaOnLambda({
        region:       LAMBDA_REGION as any,
        functionName: LAMBDA_FUNCTION,
        serveUrl:     SERVE_URL,
        composition:  compositionId,
        inputProps:   { storyboard },
        codec:        'h264',
        imageFormat:  'jpeg',
        maxRetries:   1,
        framesPerLambda: 40,
        privacy:      'private',   // S3 nesnesi private; biz indirip Supabase'e koyacağız
      })

      console.log(`[lambda] Lambda render başlatıldı: renderId=${renderId} bucket=${bucketName}`)

      // ── 2. Tamamlanmasını poll'la ───────────────────────────
      const POLL_MS    = 5_000       // 5 sn
      const MAX_WAIT   = 20 * 60_000 // 20 dk (Lambda max 15 dk + marj)
      let   outputFile : string | null = null
      const pollStart  = Date.now()

      while (Date.now() - pollStart < MAX_WAIT) {
        await new Promise(r => setTimeout(r, POLL_MS))

        const prog = await getRenderProgress({
          renderId,
          bucketName,
          functionName: LAMBDA_FUNCTION,
          region:       LAMBDA_REGION as any,
        })

        const pct = Math.round(prog.overallProgress * 100)
        if (pct % 10 === 0) {
          console.log(`[lambda] job=${job_id} ilerleme=${pct}% (${elapsed()}s)`)
        }

        if (prog.done) {
          outputFile = (prog as any).outputFile ?? null
          break
        }

        if (prog.fatalErrorEncountered) {
          const msgs = (prog.errors ?? []).map((e: any) => e.message).join('; ')
          throw new Error(`Lambda render hatası: ${msgs || 'Bilinmeyen hata'}`)
        }
      }

      if (!outputFile) {
        throw new Error(`Render ${MAX_WAIT / 60_000} dakikada tamamlanmadı — timeout`)
      }

      console.log(`[lambda] render tamam (${elapsed()}s): ${outputFile}`)

      // ── 3. S3 → Supabase ────────────────────────────────────
      let videoUrl = ''
      if (process.env.SUPABASE_URL && process.env.SUPABASE_SERVICE_ROLE_KEY) {
        // S3 key: "renders/renderId/out.mp4" veya başka format
        const s3Key = outputFile.startsWith('s3://')
          ? outputFile.split('/').slice(3).join('/')
          : outputFile
        console.log(`[lambda] S3'ten indiriliyor: s3://${bucketName}/${s3Key}`)
        const buf = await _s3Download(bucketName, s3Key)
        videoUrl  = await _supabaseUpload(buf, job_id)
        console.log(`[lambda] Supabase'e yüklendi (${(buf.length / 1024 / 1024).toFixed(1)} MB): ${videoUrl}`)
      }

      // ── 4. Backend callback ──────────────────────────────────
      await _callback(job_id, 'done', { video_url: videoUrl })
      console.log(`[lambda] job=${job_id} tamamlandı — toplam ${elapsed()}s`)

    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      console.error(`[lambda] render hatası job=${job_id} (${elapsed()}s):`, msg)
      await _callback(job_id, 'failed', { error: `${msg} (${elapsed()}s sonra)` })
    }
  })

  _processQueue()
})

// ── Health endpoint ───────────────────────────────────────────
app.get('/health', (_req, res) => {
  res.json({
    ok:               true,
    service:          'remotion-lambda-bridge',
    port:             PORT,
    lambda_function:  LAMBDA_FUNCTION  || '(eksik)',
    lambda_region:    LAMBDA_REGION,
    serve_url:        SERVE_URL ? '(ayarlı)' : '(eksik)',
    lambda_ready:     !!(LAMBDA_FUNCTION && SERVE_URL),
    render_running:   _renderRunning,
    queue_length:     _renderQueue.length,
  })
})

// ── Graceful shutdown ─────────────────────────────────────────
let _shuttingDown = false
function _shutdown(sig: string) {
  if (_shuttingDown) return
  _shuttingDown = true
  console.log(`[lambda] ${sig} — queue=${_renderQueue.length} active=${_renderRunning}`)
  setTimeout(() => { console.log('[lambda] shutdown ok'); process.exit(0) }, 8000)
}
process.on('SIGTERM', () => _shutdown('SIGTERM'))
process.on('SIGINT',  () => _shutdown('SIGINT'))
process.on('uncaughtException',  err    => { console.error('[lambda] CRASH:', err); process.exit(1) })
process.on('unhandledRejection', reason => console.error('[lambda] unhandledRejection:', reason))

// ── Başlat ───────────────────────────────────────────────────
console.log(`[lambda] Lambda Bridge başlıyor PORT=${PORT}`)
app.listen(Number(PORT), '0.0.0.0', () => {
  console.log(`[lambda] hazır → 0.0.0.0:${PORT}`)
  console.log(`[lambda] function=${LAMBDA_FUNCTION || '(eksik)'}`)
  console.log(`[lambda] region=${LAMBDA_REGION}`)
  console.log(`[lambda] serveUrl=${SERVE_URL ? '(ayarlı)' : '(eksik — REMOTION_SERVE_URL gerekli)'}`)
  if (!LAMBDA_FUNCTION || !SERVE_URL) {
    console.warn('[lambda] UYARI: Lambda yapılandırması eksik — /render 503 dönecek')
  }
})
