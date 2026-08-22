/**
 * loadFonts — yerel woff2 dosyaları (public/fonts/).
 * Harici CDN isteği yok — Lambda ağ kısıtlamasıyla uyumlu.
 *
 * Noto Sans: Regular (400), SemiBold (600), Bold (700) — Latin + LatinExt
 * KaTeX:     KaTeX_Main-Regular, KaTeX_Math-Italic
 *
 * Dosyalar git'e dahil: Regular + Bold woff2.
 * SemiBold: npm run copy-fonts ile @fontsource/noto-sans'tan kopyalanır.
 * KaTeX:    npm run copy-fonts ile katex paketinden kopyalanır.
 */
import { staticFile } from 'remotion'

// Türkçe unicode-range: U+011E-011F (Ğğ), U+015E-015F (Şş), U+0130-0131 (İı)
// LatinExt altkümesi bunları kapsar: U+0100-02AF
const NOTO_CSS = `
@font-face {
  font-family: 'AdimNoto';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url('${staticFile('fonts/NotoSans-Regular-LatinExt.woff2')}') format('woff2');
  unicode-range: U+0100-02AF, U+0304, U+0308, U+0329, U+1E00-1E9F, U+1EF2-1EFF,
                 U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'AdimNoto';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url('${staticFile('fonts/NotoSans-Regular-Latin.woff2')}') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA,
                 U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122,
                 U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'AdimNoto';
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url('${staticFile('fonts/NotoSans-SemiBold-LatinExt.woff2')}') format('woff2');
  unicode-range: U+0100-02AF, U+0304, U+0308, U+0329, U+1E00-1E9F, U+1EF2-1EFF,
                 U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'AdimNoto';
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url('${staticFile('fonts/NotoSans-SemiBold-Latin.woff2')}') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA,
                 U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122,
                 U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'AdimNoto';
  font-style: normal;
  font-weight: 700;
  font-display: swap;
  src: url('${staticFile('fonts/NotoSans-Bold-LatinExt.woff2')}') format('woff2');
  unicode-range: U+0100-02AF, U+0304, U+0308, U+0329, U+1E00-1E9F, U+1EF2-1EFF,
                 U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: 'AdimNoto';
  font-style: normal;
  font-weight: 700;
  font-display: swap;
  src: url('${staticFile('fonts/NotoSans-Bold-Latin.woff2')}') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA,
                 U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122,
                 U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
@font-face {
  font-family: 'KaTeXMain';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url('${staticFile('fonts/KaTeXMain-Regular.woff2')}') format('woff2');
}
@font-face {
  font-family: 'KaTeXMath';
  font-style: italic;
  font-weight: 400;
  font-display: swap;
  src: url('${staticFile('fonts/KaTeXMath-Italic.woff2')}') format('woff2');
}
`

// Noto Sans eski isimle de kaydet — geriye dönük uyumluluk için
// (sahne kodlarında henüz 'Noto Sans' kullananlar var)
const NOTO_ALIAS = NOTO_CSS.replace(/AdimNoto/g, 'Noto Sans')

// Module-level delayRender Lambda'da composition discovery ile gerçek render
// arasında taşınan bir handle bırakabiliyor ve 28 saniyelik timeout'a düşüyordu.
// Dosyalar bundle içindeki local static asset'lerdir; CSS'i senkron ekleyip
// font-display:swap ile render'ı ağ/font lifecycle'ına kilitlemiyoruz.
const style = document.createElement('style')
style.textContent = NOTO_CSS + NOTO_ALIAS
document.head.appendChild(style)
