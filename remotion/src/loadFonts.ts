/**
 * loadFonts — sadece yerel woff2 dosyaları (public/fonts/).
 * Harici CDN isteği yok — Lambda ağ kısıtlamasıyla uyumlu.
 *
 * Font dosyaları: public/fonts/NotoSans-{Regular,Bold}-{Latin,LatinExt}.woff2
 * Lato + Playfair Display: Noto Sans Latin kapsamından yeterli Türkçe desteği sağlanır.
 * Render bundle'a dahil edilmiş woff2'leri kullandığı için harici ağ bağımlılığı yoktur.
 */
import { delayRender, continueRender, cancelRender, staticFile } from 'remotion'

const handle = delayRender('Fontlar yükleniyor')

let _resolved = false
function done() {
  if (_resolved) return
  _resolved = true
  continueRender(handle)
}

function fail(err: unknown) {
  if (_resolved) return
  _resolved = true
  cancelRender(err instanceof Error ? err : new Error(String(err)))
}

// Yerel Noto Sans — Türkçe + Latince kapsamlı woff2
const NOTO_CSS = `
@font-face {
  font-family: 'Noto Sans';
  font-style: normal;
  font-weight: 400;
  font-display: block;
  src: url('${staticFile('fonts/NotoSans-Regular-LatinExt.woff2')}') format('woff2');
  unicode-range: U+0100-02AF, U+0304, U+0308, U+0329, U+1E00-1E9F, U+1EF2-1EFF,
                 U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Noto Sans';
  font-style: normal;
  font-weight: 400;
  font-display: block;
  src: url('${staticFile('fonts/NotoSans-Regular-Latin.woff2')}') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA,
                 U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122,
                 U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'Noto Sans';
  font-style: normal;
  font-weight: 700;
  font-display: block;
  src: url('${staticFile('fonts/NotoSans-Bold-LatinExt.woff2')}') format('woff2');
  unicode-range: U+0100-02AF, U+0304, U+0308, U+0329, U+1E00-1E9F, U+1EF2-1EFF,
                 U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'Noto Sans';
  font-style: normal;
  font-weight: 700;
  font-display: block;
  src: url('${staticFile('fonts/NotoSans-Bold-Latin.woff2')}') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA,
                 U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122,
                 U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
`

try {
  const style = document.createElement('style')
  style.textContent = NOTO_CSS
  document.head.appendChild(style)

  // Tüm yerel fontlar yüklenince handle kapat
  document.fonts.ready
    .then(done)
    .catch((err) => {
      // Noto Sans yüklenemediyse render'ı iptal et
      fail(new Error(`[loadFonts] Font yükleme hatası: ${err}`))
    })

  // 3 sn güvenlik tavanı — document.fonts.ready asılı kalırsa
  setTimeout(done, 3_000)
} catch (err) {
  fail(err)
}
