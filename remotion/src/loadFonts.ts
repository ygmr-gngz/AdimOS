/**
 * loadFonts — Remotion bundle'ı için Google Fonts yükleme.
 *
 * Bu dosya yalnızca Remotion bundle (tarayıcı/Chrome ortamı) içinde çalışır.
 * Bridge sunucusu (Node.js) tarafından import edilmez.
 *
 * Matematik sembolleri (−, ×, √, ², ≤ …) için Noto Sans şarttır;
 * Lato ve Playfair Display bu unicode bloklarını kapsamaz.
 *
 * Kullanım: src/index.ts'de import './loadFonts' satırı yeterli.
 */
import { delayRender, continueRender } from 'remotion'

const FONTS_CSS_URL =
  'https://fonts.googleapis.com/css2?' +
  'family=Lato:ital,wght@0,400;0,700;0,900;1,400&' +
  'family=Playfair+Display:ital,wght@0,700;0,900;1,700&' +
  'family=Noto+Sans:ital,wght@0,400;0,700;1,400&' +  // matematik + Türkçe fallback
  'display=swap'

const handle = delayRender('Google Fonts yükleniyor…')

function done() {
  continueRender(handle)
}

try {
  const link = document.createElement('link')
  link.rel = 'stylesheet'
  link.href = FONTS_CSS_URL
  link.addEventListener('load', () =>
    document.fonts.ready.then(done).catch(done),
  )
  link.addEventListener('error', done)   // CDN erişim hatası → render'ı engelleme
  document.head.appendChild(link)

  // 5 saniye sonra zorla devam et — Lambda timeout'u engelleme
  setTimeout(done, 5_000)
} catch {
  done()
}
