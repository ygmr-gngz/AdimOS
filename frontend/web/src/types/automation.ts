export type ContentPlatform = 'youtube' | 'instagram' | 'tiktok' | 'youtube_shorts'
export type ContentType = 'video' | 'reel' | 'short' | 'post' | 'story'
export type ContentStatus =
  | 'draft'
  | 'generating'
  | 'pending_approval'
  | 'approved'
  | 'rejected'
  | 'scheduled'
  | 'published'
  | 'failed'
  | 'error'

export interface ContentPiece {
  id: string
  title: string
  description?: string
  script?: string
  hashtags: string[]
  platform: ContentPlatform
  content_type: ContentType
  status: ContentStatus
  audio_base64?: string
  thumbnail_url?: string
  video_url?: string
  image_url?: string
  scheduled_at?: string
  published_at?: string
  created_at: string
  updated_at: string
  generated_by: 'ai' | 'manual'
  approval_notes?: string
}

export interface GenerateContentRequest {
  topic: string
  platform: ContentPlatform
  content_type: ContentType
  tone?: 'professional' | 'casual' | 'educational' | 'promotional'
  target_audience?: string
  keywords?: string[]
  duration_seconds?: number
}

export interface ApproveContentRequest {
  content_id: string
  action: 'approve' | 'reject'
  notes?: string
  scheduled_at?: string
}

export interface PublishResult {
  content_id: string
  platform: ContentPlatform
  platform_post_id?: string
  published_url?: string
  status: 'published' | 'failed'
  error?: string
}

export interface AutomationSchedule {
  id: string
  platform: ContentPlatform
  frequency: 'daily' | 'weekly' | 'custom'
  topics: string[]
  auto_publish: boolean
  is_active: boolean
  created_at: string
}
