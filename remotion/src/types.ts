// ── Storyboard JSON tipleri ───────────────────────────────────

export type VideoType = 'quiz' | 'lesson' | 'konu_anlatimi' | 'shorts' | 'motivation' | 'reel'
export type VideoFormat = '16:9' | '9:16'

// Matematik ifadesi — üç ayrı sunum formatı
export interface MathExpression {
  latex:        string  // KaTeX ile renderlama için: "\\frac{a+b}{2}"
  plain_text:   string  // KaTeX hata verirse fallback: "(a+b)/2"
  spoken_text:  string  // TTS için Türkçe: "a artı b bölü iki"
}

// Görsel varlık — Reels ve Motivation sahneleri için
export interface VisualAsset {
  visual_type:     'photo' | 'video' | 'illustration' | 'chart' | 'document' | 'icon_scene'
  visual_url:      string
  visual_prompt?:  string  // görsel üretim için ipucu
  motion?:         'zoom_in' | 'zoom_out' | 'pan_left' | 'pan_right' | 'static'
  overlay_opacity?: number  // varsayılan 0.35
}

// Eğitim Reel sahne tipi
export type ReelSegmentType = 'hook' | 'context' | 'content' | 'mistake' | 'tip' | 'outro'

// İçerik serisi tanımı
export type ContentSeries = 'cikmis_soru' | 'iki_dakikada_sgs' | 'sik_hata' | 'bir_soruda_ogren' | 'konu_anlatimi' | 'motivasyon'

export type SceneComponent =
  | 'IntroScene'
  | 'QuestionScene'
  | 'ThinkingScene'
  | 'OptionAnalysisScene'
  | 'CorrectAnswerScene'
  | 'KeyPointScene'
  | 'TransitionScene'
  | 'SummaryScene'
  | 'OutroScene'
  | 'TitleScene'
  | 'TopicIntroScene'
  | 'DefinitionScene'
  | 'BulletListScene'
  | 'QuoteScene'
  // Bölünmüş ekran soru çözümü + konu anlatımı
  | 'SplitQuizScene'
  | 'SplitQuizVerticalScene'
  | 'SplitLessonScene'
  // Muhasebe bileşenleri
  | 'JournalEntryScene'
  | 'TAccountScene'
  | 'CalculationStepsScene'
  // Motivasyon
  | 'MotivationScene'
  // İnfografik
  | 'InfographicCardGridScene'
  | 'InfographicComparisonScene'
  | 'InfographicProcessScene'
  // Konu anlatımı (LessonVideo)
  | 'LessonTitleScene'
  | 'LessonConceptScene'
  | 'LessonCardScene'
  | 'LessonExampleScene'
  | 'LessonSummaryScene'
  // Pedagojik matematik çözümü (tahta)
  | 'ChalkboardSolutionScene'
  // 2 Dakikalık Eğitim Reels
  | 'EducationalReelScene'

export interface QuizOption {
  label: string        // A, B, C, D
  text: string
  is_correct?: boolean
}

// Çözüm adımı — SplitQuizScene sağ paneli için
export interface SolutionStep {
  type: 'text' | 'formula' | 'journal_entry' | 'highlight' | 'note'
  text?: string             // text / highlight / note tiplerinde açıklama
  formula?: string          // "KDV = Matrah × %18"
  result?: string           // "= 1.800 TL"
  // journal_entry tipinde:
  debit?: { code?: string; name: string; amount: number }
  credits?: { code?: string; name: string; amount: number }[]
}

// Tahta adımı — ChalkboardSolutionScene için pedagojik yapı
export interface ChalkboardStep {
  board_text: string              // tahtada görünen denklem/metin
  voice_text?: string             // TTS için ayrı metin (raw matematik değil, konuşma dili)
  annotation?: string             // adımın altında küçük açıklama
  highlight?: string              // vurgulanan değişken veya ifade
  step_type?: 'given' | 'asked' | 'method' | 'solve' | 'verification' | 'common_mistake' | 'exam_tip' | 'answer'
  color?: 'navy' | 'blue' | 'red' | 'green' | 'amber' | 'gold'
}

// Yevmiye kaydı satırı
export interface JournalRow {
  code?: string
  name: string
  debit?: number
  credit?: number
  indent?: boolean  // alacak satırları girintili
}

// T-hesabı
export interface TAccountSide {
  label: string
  amount: number
}

// İnfografik kart
export interface InfographicCard {
  title: string
  code?: string             // hesap kodu (100, 102, 320 ...)
  category?: string         // rozet metni (AKTİF, PASİF, GELİR, GİDER ...)
  category_color?: string   // rozet rengi hex
  content?: string          // ana açıklama
  rule?: string             // kural / not
  example?: string          // örnek
  tip?: string              // püf noktası
  icon?: string             // emoji ikon
}

export interface Scene {
  id: number
  component: SceneComponent
  duration_seconds: number  // TTS süresi sonrası güncellenir
  voice_text?: string       // TTS için metin
  tts_url?: string          // Supabase'deki MP3 URL
  audio_url?: string        // alan adı normalizasyonu (tts_url alias)

  // Sahneye özel alanlar
  title?: string
  context_text?: string    // referans cümle/paragraf/şiir — soru context'i için zorunlu
  subtitle?: string
  question_text?: string
  question_number?: number
  total_questions?: number
  options?: QuizOption[]
  correct_label?: string
  explanation?: string
  highlight_option?: string
  key_point?: string
  bullet_points?: string[]
  definition?: string
  highlight_words?: string[]
  quote?: string
  quote_author?: string

  // Bölünmüş ekran soru çözümü
  solution_steps?: SolutionStep[]
  reveal_correct?: boolean     // çözüm sonunda doğru şık vurgulanır
  show_safe_area?: boolean     // Remotion preview'da güvenli alan kılavuzu göster

  // Yevmiye / T hesabı
  journal_rows?: JournalRow[]
  account_name?: string
  debit_items?: TAccountSide[]
  credit_items?: TAccountSide[]

  // Hesaplama adımları
  calculation_steps?: { label: string; value: string; is_result?: boolean }[]

  // Motivasyon
  message?: string             // ana motivasyon mesajı
  message_author?: string      // imza (opsiyonel)
  bg_variant?: 'dark' | 'gradient'

  // Konu anlatımı (SplitLessonScene)
  key_points?: string[]                                   // sol panel madde listesi
  right_panel_type?: 'ornek' | 'onemli' | 'sinav_notu'  // sağ panel renk/etiket
  right_content?: string                                  // sağ panel ana metin

  // Görsel varlık (Reels, Motivation)
  visual?: VisualAsset
  // Geriye dönük uyumluluk
  icon?: string            // emoji ikon (LessonTitleScene, LessonConceptScene)
  visual_url?: string      // fotoğraf/görsel URL (isteğe bağlı)

  // Matematik ifadeleri
  math_expressions?: MathExpression[]

  // Eğitim Reel alanları
  segment_type?: ReelSegmentType   // hook | context | content | mistake | tip | outro
  hook_text?: string               // kanca metni (0-5s)
  cta_text?: string                // call-to-action metni
  highlight_stat?: string          // vurgulanacak istatistik/rakam

  // Tahta soru çözümü (ChalkboardSolutionScene)
  given?: string[]                // verilenler: ["a - b = 32", "a = 2b"]
  asked?: string                  // istenen: "a = ?"
  method_text?: string            // yöntem açıklaması
  chalkboard_steps?: ChalkboardStep[]   // tahta adımları
  common_mistake?: string         // sık yapılan hata (kırmızı vurgu)
  exam_tip?: string               // sınav ipucu (amber)
  answer?: string                 // final cevap (yeşil kutu)

  // İnfografik
  infographic_title?: string
  infographic_subtitle?: string
  cards?: InfographicCard[]
  comparison_left?: { title: string; items: string[] }
  comparison_right?: { title: string; items: string[] }
  process_steps?: { number: number; title: string; desc: string }[]
  footer_note?: string
}

export interface BrandConfig {
  primary_color: string    // '#0B2A4A'
  secondary_color: string  // '#C9A96E'
  background_color: string // '#FAF7F0'
  font_heading: string     // 'Playfair Display'
  font_body: string        // 'Lato'
  logo_url?: string
  handle?: string          // '@adimmusavir' — marka imza için
}

export interface StoryboardJSON {
  video_type: VideoType
  title: string
  lesson_name?: string
  topic?: string
  duration_target_minutes?: number
  format: VideoFormat
  language: string
  brand: BrandConfig
  scenes: Scene[]

  // Kullanıcı süre seçimi — backend kalite kapısı için
  requested_duration_seconds?: number
  duration_tolerance_seconds?: number

  // İçerik tekrar engeleme
  content_series?: ContentSeries
  storyboard_version?: number        // "Yeniden oluştur" her seferinde artar
}

// ── Render API tipleri ────────────────────────────────────────

export interface RenderRequest {
  job_id: string
  storyboard: StoryboardJSON
  output_path?: string
}

export interface RenderResponse {
  job_id: string
  status: 'started' | 'done' | 'failed'
  video_url?: string
  error?: string
  duration_seconds?: number
}
