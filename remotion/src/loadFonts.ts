/**
 * loadFonts — yerel woff2 + Google Fonts (Lato, Playfair Display).
 *
 * Matematik sembolleri (−, ×, √, ², ≤ …) için Noto Sans şarttır;
 * woff2 dosyaları public/fonts/ içinde paketlendi — CDN bağımlılığı yok.
 *
 * Kullanım: src/index.ts'de import './loadFonts' satırı yeterli.
 */
import { delayRender, continueRender, staticFile } from 'remotion'

const handle = delayRender('Fontlar yükleniyor…')

// ── Tek-çağrı koruması — continueRender iki kez çağrılmamalı ────
let _called = false
function done() {
  if (_called) return
  _called = true
  continueRender(handle)
}

// ── Yerel Noto Sans @font-face (public/fonts/*.woff2) ────────────
const NOTO_CSS = `
@font-face {
  font-family: 'Noto Sans';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url('${staticFile('fonts/NotoSans-Regular-LatinExt.woff2')}') format('woff2');
  unicode-range: U+0100-02AF, U+0304, U+0308, U+0329, U+1E00-1E9F, U+1EF2-1EFF,
                 U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Noto Sans';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url('${staticFile('fonts/NotoSans-Regular-Latin.woff2')}') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA,
                 U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122,
                 U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Noto Sans';
  font-style: normal;
  font-weight: 700;
  font-display: swap;
  src: url('${staticFile('fonts/NotoSans-Bold-LatinExt.woff2')}') format('woff2');
  unicode-range: U+0100-02AF, U+0304, U+0308, U+0329, U+1E00-1E9F, U+1EF2-1EFF,
                 U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Noto Sans';
  font-style: normal;
  font-weight: 700;
  font-display: swap;
  src: url('${staticFile('fonts/NotoSans-Bold-Latin.woff2')}') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA,
                 U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122,
                 U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
`

const GOOGLE_FONTS_URL =
  'https://fonts.googleapis.com/css2?' +
  'family=Lato:ital,wght@0,400;0,700;0,900;1,400&' +
  'family=Playfair+Display:ital,wght@0,700;0,900;1,700&' +
  'display=swap'

try {
  // Noto Sans — yerel woff2 (CDN bağımlılığı yok)
  const style = document.createElement('style')
  style.textContent = NOTO_CSS
  document.head.appendChild(style)

  // Lato + Playfair Display — Google Fonts CDN
  const link = document.createElement('link')
  link.rel = 'stylesheet'
  link.href = GOOGLE_FONTS_URL
  link.addEventListener('load', () => document.fonts.ready.then(done).catch(done))
  link.addEventListener('error', done)   // CDN erişim hatası → render'ı engelleme
  document.head.appendChild(link)

  // 5 sn zorla devam — Lambda timeout'u engelleme
  setTimeout(done, 5_000)
} catch {
  done()
}
