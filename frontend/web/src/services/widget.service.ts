import apiClient from '@/lib/api-client'
import type {
  WidgetConversation,
  WidgetStats,
  WidgetChatResponse,
  WidgetVoiceResponse,
} from '@/types/widget'

export const widgetService = {
  async getStats(): Promise<WidgetStats> {
    const { data } = await apiClient.get<WidgetStats>('/website/stats')
    return data
  },

  async getConversations(siteId?: string): Promise<WidgetConversation[]> {
    const { data } = await apiClient.get<WidgetConversation[]>('/website/conversations', {
      params: siteId ? { site_id: siteId } : {},
    })
    return data
  },

  async getConversation(id: string): Promise<WidgetConversation> {
    const { data } = await apiClient.get<WidgetConversation>(`/website/conversations/${id}`)
    return data
  },

  async sendMessage(payload: {
    site_id: string
    message?: string
    files?: File[]
    conversation_id?: string
    visitor_id?: string
  }): Promise<WidgetChatResponse> {
    const form = new FormData()
    form.append('site_id', payload.site_id)
    if (payload.message) form.append('message', payload.message)
    if (payload.conversation_id) form.append('conversation_id', payload.conversation_id)
    if (payload.visitor_id) form.append('visitor_id', payload.visitor_id)
    payload.files?.forEach((f) => form.append('files', f))

    const { data } = await apiClient.post<WidgetChatResponse>('/website/chat', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  async sendVoice(payload: {
    site_id: string
    audio: Blob
    conversation_id?: string
    visitor_id?: string
  }): Promise<WidgetVoiceResponse> {
    const form = new FormData()
    form.append('site_id', payload.site_id)
    form.append('audio', payload.audio, 'recording.webm')
    if (payload.conversation_id) form.append('conversation_id', payload.conversation_id)
    if (payload.visitor_id) form.append('visitor_id', payload.visitor_id)

    const { data } = await apiClient.post<WidgetVoiceResponse>('/website/voice', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },
}
