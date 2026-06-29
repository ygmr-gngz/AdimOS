// ── Storyboard JSON tipleri ───────────────────────────────────

export type VideoType = 'quiz' | 'lesson' | 'shorts' | 'motivation'
export type VideoFormat = '16:9' | '9:16'

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

export interface QuizOption {
  label: string        // A, B, C, D
  text: string
  is_correct?: boolean
}

export interface Scene {
  id: number
  component: SceneComponent
  duration_seconds: number  // TTS süresi sonrası güncellenir
  voice_text?: string       // TTS için metin
  tts_url?: string          // Supabase'deki MP3 URL

  // Sahneye özel alanlar
  title?: string
  subtitle?: string
  question_text?: string
  question_number?: number
  total_questions?: number
  options?: QuizOption[]
  correct_label?: string
  explanation?: string
  highlight_option?: string  // Tek şıkkı vurgulamak için ('A', 'B' vs)
  key_point?: string
  bullet_points?: string[]
  definition?: string
  highlight_words?: string[]
  quote?: string
  quote_author?: string
}

export interface BrandConfig {
  primary_color: string    // '#0B2A4A'
  secondary_color: string  // '#C9A96E'
  background_color: string // '#FAF7F0'
  font_heading: string     // 'Playfair Display'
  font_body: string        // 'Lato'
  logo_url?: string
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
