/**
 * deploy-site.ts — Remotion bundle'ını S3'e deploy eder.
 *
 * Kullanım:
 *   npm run deploy:site
 *
 * Gerekli env değişkenleri (.env veya shell'de):
 *   REMOTION_AWS_ACCESS_KEY_ID
 *   REMOTION_AWS_SECRET_ACCESS_KEY
 *   REMOTION_AWS_REGION          (varsayılan: eu-central-1)
 *   REMOTION_AWS_BUCKET_NAME     (remotionlambda-xxxx)
 *
 * İsteğe bağlı:
 *   REMOTION_SITE_NAME           (varsayılan: adimos-video)
 *   REMOTION_LAMBDA_FUNCTION_NAME  composition doğrulaması için
 *
 * Çıktı:
 *   → serveUrl ekrana yazdırılır
 *   → Railway'de REMOTION_SERVE_URL'yi bu değerle güncelle
 */

// CJS modunda import sırası korunur — önce fs/path, sonra dotenv, sonra @remotion/lambda
import { existsSync, readFileSync } from 'fs'
import { resolve } from 'path'

// .env yükle (root veya parent dizinden)
;(function loadDotEnv() {
  const candidates = [
    resolve(process.cwd(), '..', '.env'),
    resolve(process.cwd(), '.env'),
  ]
  for (const f of candidates) {
    if (!existsSync(f)) continue
    readFileSync(f, 'utf8').split(/\r?\n/).forEach(line => {
      // KEY=value | KEY="value" | KEY='value' tüm formatları destekler
      const m = line.match(/^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(?:"([^"]*)"|'([^']*)'|(.*?))\s*$/)
      if (!m || process.env[m[1]]) return
      process.env[m[1]] = (m[2] ?? m[3] ?? m[4] ?? '').trim()
    })
    console.log(`[deploy] .env yüklendi: ${f}`)
    return
  }
  console.warn('[deploy] .env bulunamadı — shell env değişkenleri kullanılacak')
})()

// REMOTION_AWS_* → AWS_* mapping (deploySite AWS SDK kullanır)
;(['ACCESS_KEY_ID', 'SECRET_ACCESS_KEY', 'REGION'] as const).forEach(k => {
  const src = `REMOTION_AWS_${k}` as keyof NodeJS.ProcessEnv
  const dst = `AWS_${k}` as keyof NodeJS.ProcessEnv
  const val = process.env[src]
  if (val && !process.env[dst]) process.env[dst] = val
})

import path from 'path'
import { deploySite, getCompositionsOnLambda } from '@remotion/lambda'

// ── Env doğrulama ────────────────────────────────────────────────
const REQUIRED: Record<string, string | undefined> = {
  REMOTION_AWS_ACCESS_KEY_ID:     process.env.REMOTION_AWS_ACCESS_KEY_ID,
  REMOTION_AWS_SECRET_ACCESS_KEY: process.env.REMOTION_AWS_SECRET_ACCESS_KEY,
  REMOTION_AWS_BUCKET_NAME:       process.env.REMOTION_AWS_BUCKET_NAME,
}

const MISSING = Object.entries(REQUIRED)
  .filter(([, v]) => !v)
  .map(([k]) => k)

if (MISSING.length > 0) {
  console.error('[deploy] HATA — Eksik env değişkenleri:')
  MISSING.forEach(k => console.error(`  ${k}`))
  process.exit(1)
}

const REGION        = (process.env.REMOTION_AWS_REGION ?? 'eu-central-1') as Parameters<typeof deploySite>[0]['region']
const BUCKET        = process.env.REMOTION_AWS_BUCKET_NAME!
const SITE_NAME     = process.env.REMOTION_SITE_NAME ?? 'adimos-video'
const FUNCTION_NAME = process.env.REMOTION_LAMBDA_FUNCTION_NAME

const ENTRY_POINT = path.resolve(process.cwd(), 'src', 'index.ts')

const EXPECTED_COMPOSITIONS = [
  'QuizVideo',
  'SplitQuizVerticalDemo',
  'LessonVideo',
  'MotivationVideo',
  'InfographicVideo',
]

async function main(): Promise<void> {
  console.log('[deploy] ══════════════════════════════════════════════')
  console.log('[deploy] Remotion Bundle Deploy')
  console.log('[deploy] ══════════════════════════════════════════════')
  console.log(`[deploy] entry:   ${ENTRY_POINT}`)
  console.log(`[deploy] bucket:  ${BUCKET}`)
  console.log(`[deploy] site:    ${SITE_NAME}`)
  console.log(`[deploy] region:  ${REGION}`)
  console.log('')

  const { serveUrl, siteName } = await deploySite({
    entryPoint: ENTRY_POINT,
    bucketName: BUCKET,
    region:     REGION,
    siteName:   SITE_NAME,
    options: {
      onBundleProgress: (progress: number) => {
        process.stdout.write(`\r[deploy] bundle: ${Math.round(progress * 100)}%   `)
      },
      onUploadProgress: ({ totalFiles, filesUploaded, deltaSizeInBytes }: {
        totalFiles: number; filesUploaded: number; deltaSizeInBytes: number
      }) => {
        process.stdout.write(
          `\r[deploy] upload: ${filesUploaded}/${totalFiles} dosya (+${(deltaSizeInBytes / 1024).toFixed(0)} KB)   `,
        )
      },
    },
  })

  console.log('\n')
  console.log('[deploy] ✓ Bundle deploy edildi')
  console.log(`[deploy]   serveUrl: ${serveUrl}`)
  console.log(`[deploy]   siteName: ${siteName}`)

  if (FUNCTION_NAME) {
    console.log('\n[deploy] Composition listesi kontrol ediliyor…')
    try {
      const comps = await getCompositionsOnLambda({
        region:       REGION,
        functionName: FUNCTION_NAME,
        serveUrl,
        inputProps:   {},
      })
      const ids = comps.map((c: { id: string }) => c.id)
      console.log(`[deploy] Mevcut composition'lar: ${ids.join(', ')}`)
      const missing = EXPECTED_COMPOSITIONS.filter(id => !ids.includes(id))
      if (missing.length > 0) {
        console.warn(`[deploy] ⚠️  Eksik composition'lar: ${missing.join(', ')}`)
        console.warn('[deploy]    src/Root.tsx içinde kayıtlı olduklarını kontrol et')
      } else {
        console.log(`[deploy] ✓ Tüm ${EXPECTED_COMPOSITIONS.length} composition doğrulandı`)
      }
    } catch (e) {
      const msg = (e as Error).message
      console.warn(`[deploy] ⚠️  Composition kontrolü başarısız: ${msg}`)
      console.warn('[deploy]    REMOTION_LAMBDA_FUNCTION_NAME doğru ayarlı mı?')
    }
  } else {
    console.log('\n[deploy] Composition doğrulaması atlandı (REMOTION_LAMBDA_FUNCTION_NAME eksik)')
  }

  console.log('\n[deploy] ══════════════════════════════════════════════')
  console.log('[deploy] Railway ortam değişkenini güncelle:')
  console.log(`\n   REMOTION_SERVE_URL = ${serveUrl}\n`)
  console.log('[deploy] ══════════════════════════════════════════════')
}

main().catch(e => {
  console.error('\n[deploy] HATA:', (e as Error).message)
  process.exit(1)
})
