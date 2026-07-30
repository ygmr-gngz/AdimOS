/**
 * copy-fonts.mjs — Font dosyalarını node_modules'den public/fonts'a kopyalar.
 * Çalıştır: node scripts/copy-fonts.mjs
 * Otomatik: package.json prebuild scripti aracılığıyla `npm run build` öncesi.
 *
 * Kaynaklar:
 *   - NotoSans: @fontsource/noto-sans (npm install @fontsource/noto-sans@5.1.1)
 *   - KaTeX:    katex (zaten bağımlılık olarak yüklü)
 *
 * Mevcut woff2 dosyaları (git'e dahil):
 *   NotoSans-Regular-Latin.woff2, NotoSans-Regular-LatinExt.woff2
 *   NotoSans-Bold-Latin.woff2, NotoSans-Bold-LatinExt.woff2
 * Bu script onlara ek olarak SemiBold ve KaTeX fontlarını ekler.
 */

import { mkdirSync, copyFileSync, existsSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ROOT  = resolve(__dirname, '..')
const OUT   = resolve(ROOT, 'public', 'fonts')
const MODS  = resolve(ROOT, 'node_modules')

mkdirSync(OUT, { recursive: true })

const FONTS = [
  // ── Noto Sans SemiBold (weight 600) — @fontsource/noto-sans gerekli ──────
  [
    `${MODS}/@fontsource/noto-sans/files/noto-sans-latin-600-normal.woff2`,
    'NotoSans-SemiBold-Latin.woff2',
    false,  // zorunlu değil — @fontsource/noto-sans yüklüyse kopyalanır
  ],
  [
    `${MODS}/@fontsource/noto-sans/files/noto-sans-latin-ext-600-normal.woff2`,
    'NotoSans-SemiBold-LatinExt.woff2',
    false,
  ],
  // ── KaTeX fontları — katex paketi zaten bağımlılıkta ─────────────────────
  [
    `${MODS}/katex/dist/fonts/KaTeX_Main-Regular.woff2`,
    'KaTeXMain-Regular.woff2',
    true,   // zorunlu
  ],
  [
    `${MODS}/katex/dist/fonts/KaTeX_Math-Italic.woff2`,
    'KaTeXMath-Italic.woff2',
    true,   // zorunlu
  ],
]

let missingRequired = 0
let copied = 0
let skipped = 0

for (const [src, dst, required] of FONTS) {
  const dest = resolve(OUT, dst)
  if (!existsSync(src)) {
    if (required) {
      console.error(`[copy-fonts] KAYNAK YOK (zorunlu): ${src}`)
      missingRequired++
    } else {
      console.warn(`[copy-fonts] atlandı (isteğe bağlı): ${dst}`)
      skipped++
    }
    continue
  }
  copyFileSync(src, dest)
  console.log(`[copy-fonts] OK ${dst}`)
  copied++
}

console.log(`\n[copy-fonts] ${copied} kopyalandı, ${skipped} atlandı, ${missingRequired} eksik`)

if (missingRequired > 0) {
  console.error('[copy-fonts] Zorunlu font eksik — build iptal edildi.')
  process.exit(1)
}
