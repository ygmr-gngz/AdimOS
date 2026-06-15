export type VoiceState = 'idle' | 'recording' | 'processing' | 'playing' | 'error'

export interface VoiceRequest {
  audio_base64: string
  format: 'webm' | 'wav' | 'mp3'
}

export interface VoiceResponse {
  transcript: string
  intent: VoiceIntent
  answer_text: string
  answer_audio_base64: string
  agent_used: string
}

export type VoiceIntent =
  | 'knowledge_query'
  | 'crm_query'
  | 'daily_brief'
  | 'student_analysis'
  | 'general'

export interface STTResult {
  transcript: string
  confidence: number
  language: string
}
