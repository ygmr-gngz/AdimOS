import apiClient from '@/lib/api-client'

// ── Tipler ────────────────────────────────────────────────────

export type VideoType =
  | 'konu_anlatimi'
  | 'soru_cozum'
  | 'reels_short'
  | 'motivasyon'
  | 'gorsel_post'
export type VideoFormat = '16:9' | '9:16'
export type ContentTrack = 'ogrenci' | 'danisan'
export type VideoStatus =
  | 'draft'
  | 'pending'
  | 'scripting'
  | 'tts_generating'
  | 'warmup_pinging'
  | 'rendering'
  | 'ready_for_review'
  | 'approved'
  | 'queued_for_publishing'
  | 'scheduled'
  | 'published'
  | 'rejected'
  | 'failed'
  | 'archived'

export interface VideoScene {
  id: string
  job_id: string
  scene_index: number
  component: string
  duration_seconds: number
  data: Record<string, unknown>
  voice_text?: string
  tts_url?: string
  status: 'pending' | 'tts_done' | 'render_done' | 'failed'
}

export type CardStillBackground = 'canvas' | 'navy' | 'white'

export const CARD_STILL_BACKGROUND_LABELS: Record<CardStillBackground, string> = {
  canvas: 'Açık (varsayılan)',
  navy:   'Lacivert',
  white:  'Beyaz',
}

export interface PublishPackage {
  card_stills?: string[]
  card_stills_background?: CardStillBackground
  [key: string]: unknown
}

export interface VideoJob {
  id: string
  type: VideoType
  title: string
  lesson_name?: string
  topic?: string
  format: VideoFormat
  target_duration_minutes?: number
  storyboard?: Record<string, unknown>
  status: VideoStatus
  video_url?: string
  error_message?: string
  created_at: string
  updated_at: string
  scenes?: VideoScene[]
  publish_package?: PublishPackage
}

export interface CreateVideoPayload {
  type: VideoType
  title?: string
  lesson_name?: string
  topic?: string
  description?: string
  format: VideoFormat
  target_duration_minutes?: number
  requested_duration_seconds?: number   // saniye cinsinden (backend kalite kapısı için zorunlu)
  duration_tolerance_seconds?: number   // varsayılan 8 saniye
  pre_storyboard?: Record<string, unknown>
  infographic_template?: string
  content_series?: string
  content_track: ContentTrack   // M8: backend'de zorunlu — burada da opsiyonel bırakılmadı
  storyboard_version?: number
  questions?: {
    text: string
    options: { label: string; text: string }[]
    correct_label: string
    explanation?: string
  }[]
}

// ── Durum bilgisi ─────────────────────────────────────────────

export const VIDEO_STATUS_LABELS: Record<VideoStatus, string> = {
  draft: 'Taslak',
  pending: 'Bekliyor',
  scripting: 'Senaryo yazılıyor',
  tts_generating: 'Ses üretiliyor',
  warmup_pinging: 'Render servisi hazırlanıyor',
  rendering: 'Video oluşturuluyor',
  ready_for_review: 'İnceleme bekliyor',
  approved: 'Onaylandı',
  queued_for_publishing: 'Yayın kuyruğunda',
  scheduled: 'Planlandı',
  published: 'Yayınlandı',
  rejected: 'Reddedildi',
  failed: 'Hata',
  archived: 'Arşivlendi',
}

export const VIDEO_STATUS_COLORS: Record<VideoStatus, string> = {
  draft: '#94a3b8',
  pending: '#94a3b8',
  scripting: '#f59e0b',
  tts_generating: '#f59e0b',
  warmup_pinging: '#0ea5e9',
  rendering: '#3b82f6',
  ready_for_review: '#8b5cf6',
  approved: '#10b981',
  queued_for_publishing: '#0ea5e9',
  scheduled: '#0ea5e9',
  published: '#059669',
  rejected: '#ef4444',
  failed: '#ef4444',
  archived: '#64748b',
}

export const VIDEO_TYPE_LABELS: Record<VideoType, string> = {
  konu_anlatimi: 'Konu Anlatımı',
  soru_cozum:    'Soru Çözüm',
  reels_short:   'Reels / Short',
  motivasyon:    'Motivasyon',
  gorsel_post:   'Görsel Post',
}

// Geriye dönük uyumluluk — eski DB kayıtları eski tip adlarıyla saklanmış olabilir
export const VIDEO_TYPE_LABEL_FALLBACK: Record<string, string> = {
  quiz: 'Soru Çözüm', lesson: 'Ders Anlatımı', shorts: 'Reels / Short',
  motivation: 'Motivasyon', infographic: 'Görsel Post',
}

export function getTypeLabel(type: string): string {
  return VIDEO_TYPE_LABELS[type as VideoType]
    ?? VIDEO_TYPE_LABEL_FALLBACK[type]
    ?? type
}

// ── Service ───────────────────────────────────────────────────

const videoService = {
  async createJob(payload: CreateVideoPayload): Promise<VideoJob> {
    const { data } = await apiClient.post('/video/create', payload)
    return data
  },

  async listJobs(type?: VideoType): Promise<VideoJob[]> {
    const params = type ? { type } : {}
    const { data } = await apiClient.get('/video/jobs', { params })
    return data
  },

  async getJob(id: string): Promise<VideoJob> {
    const { data } = await apiClient.get(`/video/jobs/${id}`)
    return data
  },

  async approveJob(id: string): Promise<void> {
    await apiClient.post(`/video/jobs/${id}/approve`)
  },

  async rejectJob(id: string, reason?: string): Promise<void> {
    await apiClient.post(`/video/jobs/${id}/reject`, { reason })
  },

  async regenerateScene(sceneId: string): Promise<VideoScene> {
    const { data } = await apiClient.post(`/video/scenes/${sceneId}/regenerate`)
    return data
  },

  async regenerateJob(jobId: string): Promise<VideoJob> {
    const { data } = await apiClient.post(`/video/jobs/${jobId}/regenerate`)
    return data
  },

  async regenerateCardStills(jobId: string, background: CardStillBackground): Promise<{
    ok: boolean; background: CardStillBackground; card_stills: string[]
  }> {
    const { data } = await apiClient.post(`/video/jobs/${jobId}/card-stills`, { background })
    return data
  },

  async renderHealth(): Promise<{ circuit_open: boolean; consecutive_failures: number; threshold: number }> {
    const { data } = await apiClient.get('/video/render-health')
    return data
  },

  async resetCircuit(): Promise<void> {
    await apiClient.post('/video/render-health/reset')
  },
}

export default videoService
