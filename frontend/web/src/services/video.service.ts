import apiClient from '@/lib/api-client'

// ── Tipler ────────────────────────────────────────────────────

export type VideoType = 'quiz' | 'lesson' | 'shorts' | 'motivation'
export type VideoFormat = '16:9' | '9:16'
export type VideoStatus =
  | 'draft'
  | 'pending'
  | 'scripting'
  | 'tts_generating'
  | 'rendering'
  | 'ready_for_review'
  | 'approved'
  | 'queued_for_publishing'
  | 'scheduled'
  | 'published'
  | 'rejected'
  | 'failed'

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
}

export interface CreateVideoPayload {
  type: VideoType
  title?: string
  lesson_name?: string
  topic?: string
  description?: string
  format: VideoFormat
  target_duration_minutes?: number
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
  rendering: 'Video oluşturuluyor',
  ready_for_review: 'İnceleme bekliyor',
  approved: 'Onaylandı',
  queued_for_publishing: 'Yayın kuyruğunda',
  scheduled: 'Planlandı',
  published: 'Yayınlandı',
  rejected: 'Reddedildi',
  failed: 'Hata',
}

export const VIDEO_STATUS_COLORS: Record<VideoStatus, string> = {
  draft: '#94a3b8',
  pending: '#94a3b8',
  scripting: '#f59e0b',
  tts_generating: '#f59e0b',
  rendering: '#3b82f6',
  ready_for_review: '#8b5cf6',
  approved: '#10b981',
  queued_for_publishing: '#0ea5e9',
  scheduled: '#0ea5e9',
  published: '#059669',
  rejected: '#ef4444',
  failed: '#ef4444',
}

export const VIDEO_TYPE_LABELS: Record<VideoType, string> = {
  quiz: 'Soru Çözüm',
  lesson: 'Ders Anlatımı',
  shorts: 'Reels / Shorts',
  motivation: 'Motivasyon',
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
}

export default videoService
