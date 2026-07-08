/**
 * Remotion Render Server — Railway'de ayrı bir Node.js servisi olarak çalışır.
 * FastAPI backend bu servisi HTTP ile çağırır.
 */
import express from 'express'
import path from 'path'
import fs from 'fs'
import { bundle } from '@remotion/bundler'
import { renderMedia, selectComposition } from '@remotion/renderer'
import { StoryboardJSON, RenderRequest, RenderResponse } from '../types'
import { DIMENSIONS, FPS } from '../brand'
import { getTotalFrames } from '../utils'

const app = express()
app.use(express.json({ limit: '10mb' }))

const PORT = process.env.PORT || 3001
const OUT_DIR = process.env.OUT_DIR || path.join(process.cwd(), 'out')

// ── Render kuyruk sistemi (max 1 eşzamanlı render) ────────────
// OOM koruması: Railway memory sınırını aşmamak için renderlar sıralanır.
// Her render ayrı Chromium örneği açar; eşzamanlı render = katlanır RAM.
let _renderRunning = false
const _renderQueue: Array<() => Promise<void>> = []

async function _processRenderQueue() {
  if (_renderRunning || _renderQueue.length === 0) return
  _renderRunning = true
  const task = _renderQueue.shift()!
  try {
    await task()
  } finally {
    _renderRunning = false
    _processRenderQueue()  // bir sonraki görevi başlat
  }
}

function _logMemory(tag: string) {
  const mem = process.memoryUsage()
  console.log(
    `[remotion] ${tag} | RSS=${Math.round(mem.rss / 1024 / 1024)}MB ` +
    `Heap=${Math.round(mem.heapUsed / 1024 / 1024)}/${Math.round(mem.heapTotal / 1024 / 1024)}MB`
  )
}

// Supabase yükleme (isteğe bağlı — job_id ile hedef URL belirlenir)
async function uploadToSupabase(filePath: string, jobId: string): Promise<string> {
  const { createClient } = await import('@supabase/supabase-js')
  const supabase = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  )
  const data = fs.readFileSync(filePath)
  const remotePath = `videos/${jobId}.mp4`
  await supabase.storage.from('video-outputs').upload(remotePath, data, {
    contentType: 'video/mp4', upsert: true,
  })
  const { data: urlData } = supabase.storage.from('video-outputs').getPublicUrl(remotePath)
  return urlData.publicUrl
}

// Bundle bir kez hazır tutulur (restart'ta yeniden oluşturulur)
let bundleLocation: string | null = null
async function getBundle(): Promise<string> {
  if (bundleLocation) return bundleLocation
  console.log('[remotion] bundle oluşturuluyor...')
  bundleLocation = await bundle({ entryPoint: path.join(process.cwd(), 'src/index.ts') })
  console.log('[remotion] bundle hazır:', bundleLocation)
  return bundleLocation
}

// ── Render endpoint ───────────────────────────────────────────

app.post('/render', (req, res) => {
  const body = req.body as RenderRequest
  const { job_id, storyboard } = body

  if (!job_id || !storyboard) {
    return res.status(400).json({ error: 'job_id ve storyboard gerekli' })
  }

  const queuePos = _renderQueue.length
  console.log(`[remotion] render kuyruğa alındı: job=${job_id} tip=${storyboard.video_type} sıra=${queuePos} aktif=${_renderRunning}`)

  // Hemen yanıt dön; render arka planda sırayla çalışır
  res.json({ job_id, status: 'started', queue_position: queuePos } as RenderResponse & { queue_position: number })

  // Görevi kuyruğa ekle
  _renderQueue.push(async () => {
    const startTime = Date.now()
    console.log(`[remotion] render başlıyor: job=${job_id} tip=${storyboard.video_type}`)
    _logMemory(`render-start job=${job_id}`)

    try {
      if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true })
      const outPath = path.join(OUT_DIR, `${job_id}.mp4`)

      const bundlePath = await getBundle()
      const dim = DIMENSIONS[storyboard.format]
      const totalFrames = getTotalFrames(storyboard)

      const browserExecutable = process.env.BROWSER_EXECUTABLE_PATH || undefined
      if (browserExecutable) {
        console.log(`[remotion] browser: ${browserExecutable}`)
      }

      const compositionId =
        storyboard.video_type === 'motivation'    ? 'MotivationVideo' :
        storyboard.video_type === 'lesson'        ? 'InfographicVideo' :
        storyboard.video_type === 'konu_anlatimi' ? 'QuizVideo' :
        'QuizVideo'

      console.log(`[remotion] kompozisyon seçiliyor: ${compositionId} frames=${totalFrames} ${dim.width}x${dim.height}`)

      const comp = await selectComposition({
        serveUrl: bundlePath,
        id: compositionId,
        inputProps: { storyboard },
        browserExecutable,
      })

      await renderMedia({
        composition: {
          ...comp,
          durationInFrames: totalFrames,
          width: dim.width,
          height: dim.height,
        },
        serveUrl: bundlePath,
        codec: 'h264',
        outputLocation: outPath,
        inputProps: { storyboard },
        browserExecutable,
        // OOM koruması: tek Chromium sekmesi (varsayılan = CPU sayısı kadar paralel)
        concurrency: 1,
        onProgress: ({ progress }) => {
          const pct = Math.round(progress * 100)
          if (pct % 10 === 0) {
            console.log(`[remotion] job=${job_id} ilerleme=${pct}%`)
            if (pct === 50) _logMemory(`render-50pct job=${job_id}`)
          }
        },
      })

      const elapsed = Math.round((Date.now() - startTime) / 1000)
      console.log(`[remotion] render tamam: ${outPath} (${elapsed}s)`)
      _logMemory(`render-done job=${job_id}`)

      // Supabase'e yükle ve backend'i bilgilendir
      let videoUrl = ''
      if (process.env.SUPABASE_URL && process.env.SUPABASE_SERVICE_ROLE_KEY) {
        videoUrl = await uploadToSupabase(outPath, job_id)
        console.log(`[remotion] yüklendi: ${videoUrl}`)
      }

      if (process.env.BACKEND_URL) {
        await fetch(`${process.env.BACKEND_URL}/video/render-callback`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ job_id, status: 'done', video_url: videoUrl }),
        }).catch(e => console.warn('[remotion] callback hatası:', e.message))
      }

      // Çıktı dosyasını temizle (Railway disk alanı sınırlı)
      try { fs.unlinkSync(outPath) } catch {}

    } catch (err) {
      const elapsed = Math.round((Date.now() - startTime) / 1000)
      const error = err instanceof Error ? err.message : String(err)
      console.error(`[remotion] render hatası job=${job_id} (${elapsed}s):`, error)
      _logMemory(`render-error job=${job_id}`)

      if (process.env.BACKEND_URL) {
        await fetch(`${process.env.BACKEND_URL}/video/render-callback`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ job_id, status: 'failed', error: `${error} (${elapsed}s sonra)` }),
        }).catch(() => {})
      }
    }
  })

  _processRenderQueue()
})

app.get('/health', (_req, res) => {
  _logMemory('health-check')
  res.json({
    ok: true,
    service: 'remotion',
    bundle_ready: !!bundleLocation,
    port: PORT,
    render_running: _renderRunning,
    queue_length: _renderQueue.length,
  })
})

// ── Graceful shutdown (Railway SIGTERM gönderir önce) ────────
let _shuttingDown = false

function gracefulShutdown(signal: string) {
  if (_shuttingDown) return
  _shuttingDown = true
  console.log(`[remotion] ${signal} alındı — render kuyruğu=${_renderQueue.length} aktif=${_renderRunning}`)
  // Railway ~ 10s timeout verir; aktif render bitmezse process ölür
  setTimeout(() => {
    console.log('[remotion] graceful shutdown tamamlandı')
    process.exit(0)
  }, 8000)
}

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'))
process.on('SIGINT',  () => gracefulShutdown('SIGINT'))

process.on('uncaughtException', (err) => {
  console.error('[remotion] CRASH uncaughtException:', err)
  _logMemory('crash')
  process.exit(1)
})

process.on('unhandledRejection', (reason) => {
  console.error('[remotion] unhandledRejection:', reason)
})

// Railway ve diğer cloud ortamlarında 0.0.0.0 üzerinde dinlemeli
console.log(`[remotion] sunucu başlıyor PORT=${PORT}`)
app.listen(Number(PORT), '0.0.0.0', () => {
  console.log(`[remotion] render server 0.0.0.0:${PORT} portunda çalışıyor`)
  console.log(`[remotion] NODE_VERSION=${process.version} BROWSER=${process.env.BROWSER_EXECUTABLE_PATH || '(yok)'}`)
  _logMemory('startup')
  getBundle().catch(e => console.error('[remotion] bundle hatası:', e))
})
