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
import { getTotalFrames } from '../compositions/QuizVideo'

const app = express()
app.use(express.json({ limit: '10mb' }))

const PORT = process.env.PORT || 3001
const OUT_DIR = process.env.OUT_DIR || path.join(process.cwd(), 'out')

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
  bundleLocation = await bundle({ entryPoint: path.join(__dirname, '../index.ts') })
  console.log('[remotion] bundle hazır:', bundleLocation)
  return bundleLocation
}

// ── Render endpoint ───────────────────────────────────────────

app.post('/render', async (req, res) => {
  const body = req.body as RenderRequest
  const { job_id, storyboard } = body

  if (!job_id || !storyboard) {
    return res.status(400).json({ error: 'job_id ve storyboard gerekli' })
  }

  console.log(`[remotion] render başladı: job=${job_id} tip=${storyboard.video_type}`)

  // Hemen "started" dön, render arka planda devam eder
  res.json({ job_id, status: 'started' } as RenderResponse)

  try {
    if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true })
    const outPath = path.join(OUT_DIR, `${job_id}.mp4`)

    const bundlePath = await getBundle()
    const dim = DIMENSIONS[storyboard.format]
    const totalFrames = getTotalFrames(storyboard)

    const comp = await selectComposition({
      serveUrl: bundlePath,
      id: 'QuizVideo',
      inputProps: { storyboard },
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
      onProgress: ({ progress }) => {
        if (Math.round(progress * 100) % 10 === 0) {
          console.log(`[remotion] job=${job_id} ilerleme=${Math.round(progress * 100)}%`)
        }
      },
    })

    console.log(`[remotion] render tamam: ${outPath}`)

    // Supabase'e yükle ve backend'i bilgilendir
    let videoUrl = ''
    if (process.env.SUPABASE_URL && process.env.SUPABASE_SERVICE_ROLE_KEY) {
      videoUrl = await uploadToSupabase(outPath, job_id)
      console.log(`[remotion] yüklendi: ${videoUrl}`)
    }

    // Backend'e render tamamlandı bildirimi
    if (process.env.BACKEND_URL) {
      await fetch(`${process.env.BACKEND_URL}/video/render-callback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id, status: 'done', video_url: videoUrl }),
      }).catch(e => console.warn('[remotion] callback hatası:', e.message))
    }
  } catch (err) {
    const error = err instanceof Error ? err.message : String(err)
    console.error(`[remotion] render hatası job=${job_id}:`, error)

    if (process.env.BACKEND_URL) {
      await fetch(`${process.env.BACKEND_URL}/video/render-callback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id, status: 'failed', error }),
      }).catch(() => {})
    }
  }
})

app.get('/health', (_req, res) => {
  res.json({ ok: true, service: 'remotion', bundle_ready: !!bundleLocation, port: PORT })
})

// Railway ve diğer cloud ortamlarında 0.0.0.0 üzerinde dinlemeli
app.listen(Number(PORT), '0.0.0.0', () => {
  console.log(`[remotion] render server 0.0.0.0:${PORT} portunda çalışıyor`)
  getBundle().catch(e => console.error('[remotion] bundle hatası:', e))
})
