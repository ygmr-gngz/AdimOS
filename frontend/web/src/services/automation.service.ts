import apiClient from '@/lib/api-client'
import type {
  ContentPiece,
  GenerateContentRequest,
  PublishResult,
} from '@/types/automation'

export const automationService = {
  async generateContent(request: GenerateContentRequest): Promise<{ content_id: string; status: string }> {
    const type = request.type ?? 'video'
    const { data } = await apiClient.post(`/content/${type}/generate`, {
      topic: request.topic,
      duration_minutes: request.duration_minutes ?? 5,
    })
    return data
  },

  async listContent(): Promise<ContentPiece[]> {
    const { data } = await apiClient.get('/content')
    return Array.isArray(data) ? data : []
  },

  async getContent(contentId: string): Promise<ContentPiece> {
    const { data } = await apiClient.get(`/content/${contentId}`)
    return data
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
