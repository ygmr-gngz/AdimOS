/**
 * Tasarım token'ları — tüm sahneler sadece bu değerleri kullanır.
 * Hex kodu doğrudan sahne koduna yazılmaz.
 */
export const T = {
  color: {
    navy900:   "#0B2545",   // ana koyu zemin, başlık bloğu, footer
    navy700:   "#15355F",
    navy500:   "#2C6FB5",   // bilgi mavisi (Aktif rozet)
    surface:   "#FFFFFF",   // kart zemini
    canvas:    "#F4F6FA",   // sayfa zemini
    quizFrame: "#A3DBFA",   // QuizBoardVideo çerçeve
    quizBar:   "#9DE1FF",   // QuizBoardVideo ilerleme çubuğu
    quizCard:  "#FDFDFB",   // QuizBoardVideo kart zemini
    gold:      "#E8B04B",   // vurgu / alt başlık / CTA çizgisi
    green:     "#2E7D5B",   // Aktif (A)
    purple:    "#6B4C9A",   // Pasif (P)
    blue:      "#2C6FB5",   // Gelir (G)
    orange:    "#E2703A",   // Gider (Gi)
    danger:    "#C0392B",   // sık yapılan hata
    answerRed: "#D32F2F",   // yanlış cevap vurgusu
    text:      "#1B2A41",
    muted:     "#5B6B82",
    border:    "#E1E7F0",
  },
  radius: { card: 24, quizCard: 28, badge: 999, chip: 12 },
  shadow: { card: "0 8px 24px rgba(11,37,69,0.10)" },
  space:  { xs: 8, sm: 16, md: 24, lg: 40, xl: 64 },
  font: {
    display: "'Noto Sans', sans-serif",
    body:    "'Noto Sans', sans-serif",
    math:    "'KaTeXMain', 'KaTeX_Main', serif",
  },
  size9x16: { title: 92, subtitle: 58, body: 46, caption: 62, code: 40 },
  size16x9: { title: 76, subtitle: 48, body: 38, caption: 40, code: 34 },
  safe9x16: { top: 220, bottom: 320, x: 72 },
  safe16x9: { top: 60,  bottom: 90,  x: 80 },

  // Hesap niteliği → renk
  natureColor: (nature: "A" | "P" | "G" | "Gi" | string): string => {
    switch (nature) {
      case "A":  return "#2E7D5B"  // Aktif — yeşil
      case "P":  return "#6B4C9A"  // Pasif — mor
      case "G":  return "#2C6FB5"  // Gelir — mavi
      case "Gi": return "#E2703A"  // Gider — turuncu
      default:   return "#5B6B82"
    }
  },
} as const
