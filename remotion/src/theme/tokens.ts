/**
 * Tasarım token'ları — tüm sahneler sadece bu değerleri kullanır.
 * Hex kodu ve çıplak piksel değeri doğrudan sahne koduna yazılamaz.
 * Değerler referans infografikten piksel düzeyinde ölçülmüştür.
 */
export const T = {
  color: {
    // ── Marka lacivertleri ─────────────────────────────────────────
    navy900:   "#001645",   // ana marka lacivertı, başlık, koyu blok, footer
    navy800:   "#0A0E21",   // footer bandı
    navy700:   "#173277",   // Gelir (G) rozeti
    navy500:   "#1B458C",   // ikincil mavi

    // ── Hesap niteliği renkleri (DEĞİŞTİRİLEMEZ) ──────────────────
    green700:  "#1E4B2F",   // AKTİF (A) — Borç artar, Alacak azalır
    purple700: "#491C74",   // PASİF (P) — Borç azalır, Alacak artar
    orange600: "#BD6246",   // GİDER (Gi) — Borç artar, Alacak azalır
    gold500:   "#BF8D4B",   // alt başlık, ayraç, vurgu

    // ── Anlam renkleri ─────────────────────────────────────────────
    crimson:   "#CE425C",   // uyarı, yanlış kayıt, hata
    answerRed: "#D32F2F",   // yanlış cevap vurgusu (quiz)

    // ── Quiz özel ─────────────────────────────────────────────────
    quizFrame: "#A3DBFA",   // QuizBoardVideo dış çerçeve
    quizBar:   "#9DE1FF",   // QuizBoardVideo üst bar
    quizCard:  "#FDFDFB",   // QuizBoardVideo kart zemini

    // ── Yüzeyler ──────────────────────────────────────────────────
    surface:   "#FBFBFB",   // kart zemini
    canvas:    "#F4F6FA",   // sayfa zemini — surface'tan (FBFBFB) belirgin ayrışsın
                            // diye (eskiden FEFEFE idi, surface'la aşırı yakındı —
                            // ölçüm: içerik pikseli %7'de tıkalı kalıyordu, beyaz
                            // üstü beyaz kart "arka plandan farklı piksel" sayılmıyordu)
    border:    "#E1E7F0",   // kenar çizgisi

    // ── Metin ────────────────────────────────────────────────────
    text:      "#1B2A41",
    muted:     "#5B6B82",
  },

  // ── Hesap niteliği → renk (DEĞİŞTİRİLEMEZ) ──────────────────────
  // Borç/Alacak cümlesi bu fonksiyondan türetilir, LLM yazamaz.
  natureColor: (nature: "A" | "P" | "G" | "Gi" | string): string => {
    switch (nature) {
      case "A":  return "#1E4B2F"   // Aktif
      case "P":  return "#491C74"   // Pasif
      case "G":  return "#173277"   // Gelir
      case "Gi": return "#BD6246"   // Gider
      default:   return "#5B6B82"
    }
  },

  // ── Hesap niteliği → Borç/Alacak kuralı (props'tan gelmez) ───────
  natureRule: (nature: "A" | "P" | "G" | "Gi" | string): string => {
    switch (nature) {
      case "A":  return "Borç artar, Alacak azalır."
      case "P":  return "Borç azalır, Alacak artar."
      case "G":  return "Borç azalır, Alacak artar."
      case "Gi": return "Borç artar, Alacak azalır."
      default:   return ""
    }
  },

  // ── Köşe yarıçapları ─────────────────────────────────────────────
  radius: {
    card:      28,
    cardLg:    24,
    badge:     999,
    chip:      16,
    tip:       16,
    codeBadge: 10,
  },

  // ── Gölge ────────────────────────────────────────────────────────
  shadow: {
    card: "0 8px 24px rgba(0,22,69,0.10)",
  },

  // ── Boşluk ───────────────────────────────────────────────────────
  space: { xs: 8, sm: 16, md: 24, lg: 40, xl: 64 },

  // ── Font yüzleri ─────────────────────────────────────────────────
  font: {
    display: "'Noto Sans', sans-serif",
    body:    "'Noto Sans', sans-serif",
    math:    "'KaTeXMain', 'KaTeX_Main', serif",
  },

  // ── Layout 9:16 (1080×1920) ──────────────────────────────────────
  layout9x16: {
    // Güvenli alanlar
    safeTop:    220,
    safeBottom: 320,
    safeX:      60,
    // Kart
    cardW:      960,
    cardPad:    56,
    cardRadius: 28,
    // Sabit boyutlar — LLM'den gelen değişken uzunlukta metin DEĞİL
    // (hesap kodu/nitelik harfi sabit uzunlukta), dinamik ölçeklemeye dahil değil.
    codeBadgeFont: 56,
    natureBadge:   56,
    captionFont:   30,
    // Dinamik ölçeklenen alanlar — target: kısa içerikte kullanılan tavan,
    // min: taşma durumunda tek bir scale katsayısıyla inebileceği taban.
    // Taban altına inmeden sığmıyorsa layout_overflow fırlatılır (sessiz
    // kırpma yok — v4 spesifikasyonundaki kuralla aynı).
    font: {
      title: { target: 92, min: 68 },
      body:  { target: 50, min: 38 },
      label: { target: 34, min: 28 },
      entry: { target: 34, min: 30 },
      tip:   { target: 34, min: 30 },
    },
    // Düzen
    sectionGap:  44,
    iconSize:    28,
    entryIndent: 48,
  },

  // ── Layout 16:9 (1920×1080) ──────────────────────────────────────
  layout16x9: {
    // Güvenli alanlar
    safeTop:    60,
    safeBottom: 90,
    safeX:      80,
    // Kart
    cardW:      1180,
    cardPad:    32,
    cardRadius: 24,
    // Tipografi
    codeBadgeFont: 40,
    natureBadge:   40,
    captionFont:   22,
    // 16:9 için min değerleri hiç ölçülmedi/belirtilmedi — min=target koyarak
    // dinamik ölçeklemeyi bu format için etkisiz bırakıyoruz (şimdilik sabit
    // davranış korunuyor). Gerçek 16:9 kart kullanımı gündeme gelince ayrıca
    // ölçülüp ayarlanmalı, buradan tahminle doldurulmadı.
    font: {
      title: { target: 34, min: 34 },
      body:  { target: 27, min: 27 },
      label: { target: 24, min: 24 },
      entry: { target: 25, min: 25 },
      tip:   { target: 27, min: 27 },
    },
    // Düzen
    sectionGap:  16,
    iconSize:    22,
    entryIndent: 34,
  },

  // ── Geriye dönük uyumluluk (eski sahneler için) ──────────────────
  safe9x16:  { top: 220, bottom: 320, x: 72 },
  safe16x9:  { top: 60,  bottom: 90,  x: 80 },
  size9x16:  { title: 48, subtitle: 38, body: 38, caption: 30, code: 56 },
  size16x9:  { title: 34, subtitle: 26, body: 27, caption: 22, code: 40 },
} as const
