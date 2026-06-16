import apiClient from '@/lib/api-client'
import type {
  ContentPiece,
  GenerateContentRequest,
  ApproveContentRequest,
  PublishResult,
} from '@/types/automation'

const TYPE_TO_BACKEND: Record<string, string> = {
  video: 'video',
  short: 'short',
  reel: 'short',
  post: 'post',
  story: 'post',
}

const PLATFORM_TO_BACKEND: Record<string, string> = {
  youtube: 'video',
  youtube_shorts: 'short',
  instagram: 'post',
  tiktok: 'short',
}

export const automationService = {
  async generateContent(request: GenerateContentRequest): Promise<ContentPiece> {
    const backendType =
      TYPE_TO_BACKEND[request.content_type] ??
      PLATFORM_TO_BACKEND[request.platform] ??
      'video'
    const durationMinutes = request.duration_seconds
      ? Math.ceil(request.duration_seconds / 60)
      : 5
    const { data } = await apiClient.post(`/content/${backendType}/generate`, {
      topic: request.topic,
      duration_minutes: durationMinutes,
    })
    return {
      id: data.content_id,
      title: request.topic,
      hashtags: [],
      platform: request.platform,
      content_type: request.content_type,
      status: 'draft',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      generated_by: 'ai',
    }
  },

  async listContent(filter?: string): Promise<ContentPiece[]> {
    const { data } = await apiClient.get('/content')
    const raw = Array.isArray(data) ? data : []
    const items: ContentPiece[] = raw.map((item: Record<string, unknown>) => ({
      id: String(item.id ?? ''),
      title: String(item.title ?? item.topic ?? 'İsimsiz'),
      description: item.caption ? String(item.caption) : undefined,
      hashtags: Array.isArray(item.hashtags) ? item.hashtags : [],
      platform: (item.platform as ContentPiece['platform']) ?? 'youtube',
      content_type: (item.type as ContentPiece['content_type']) ?? 'video',
      status: (item.status as ContentPiece['status']) ?? 'draft',
      video_url: item.video_url ? String(item.video_url) : undefined,
      audio_url: item.audio_url ? String(item.audio_url) : undefined,
      created_at: String(item.created_at ?? new Date().toISOString()),
      updated_at: String(item.updated_at ?? item.created_at ?? new Date().toISOString()),
      generated_by: 'ai',
      approval_notes: item.approval_notes ? String(item.approval_notes) : undefined,
    }))
    return filter ? items.filter((c) => c.status === filter) : items
  },

  async getContent(contentId: string): Promise<ContentPiece> {
    const { data } = await apiClient.get(`/content/${contentId}`)
    return data as ContentPiece
  },

  async approveContent(req: ApproveContentRequest): Promise<ContentPiece> {
    const { data } = await apiClient.patch(`/content/${req.content_id}/approve`, {
      action: req.action,
      notes: req.notes ?? '',
    })
    const item = data as Record<string, unknown>
    return {
      id: String(item.id ?? req.content_id),
      title: String(item.title ?? item.topic ?? 'İsimsiz'),
      description: item.caption ? String(item.caption) : undefined,
      hashtags: Array.isArray(item.hashtags) ? item.hashtags : [],
      platform: (item.platform as ContentPiece['platform']) ?? 'youtube',
      content_type: (item.type as ContentPiece['content_type']) ?? 'video',
      status: (item.status as ContentPiece['status']) ?? (req.action === 'approve' ? 'approved' : 'rejected'),
      video_url: item.video_url ? String(item.video_url) : undefined,
      audio_url: item.audio_url ? String(item.audio_url) : undefined,
      created_at: String(item.created_at ?? new Date().toISOString()),
      updated_at: String(item.updated_at ?? new Date().toISOString()),
      generated_by: 'ai',
      approval_notes: item.approval_notes ? String(item.approval_notes) : undefined,
    }
  },

  async publishContent(contentId: string): Promise<PublishResult> {
    const { data } = await apiClient.post(`/content/${contentId}/publish`)
    return data as PublishResult
  },

  async publishToYoutube(contentId: string): Promise<PublishResult> {
    const { data } = await apiClient.post(`/content/${contentId}/publish/youtube`)
    return data
  },

  async publishToInstagram(contentId: string): Promise<PublishResult> {
    const { data } = await apiClient.post(`/content/${contentId}/publish/instagram`)
    return data
  },

  async deleteContent(contentId: string): Promise<void> {
    await apiClient.delete(`/content/${contentId}`)
  },
}
