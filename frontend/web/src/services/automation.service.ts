import apiClient from '@/lib/api-client'
import type {
  ContentPiece,
  GenerateContentRequest,
  ApproveContentRequest,
  PublishResult,
  AutomationSchedule,
} from '@/types/automation'

export const automationService = {
  async generateContent(request: GenerateContentRequest): Promise<ContentPiece> {
    const { data } = await apiClient.post('/automation/generate', request)
    return data
  },

  async listContent(status?: string): Promise<{ content: ContentPiece[]; total: number }> {
    const params = status ? { status } : {}
    const { data } = await apiClient.get('/automation/content', { params })
    return data
  },

  async approveContent(request: ApproveContentRequest): Promise<ContentPiece> {
    const { data } = await apiClient.post('/automation/approve', request)
    return data
  },

  async publishContent(contentId: string): Promise<PublishResult> {
    const { data } = await apiClient.post(`/automation/publish/${contentId}`)
    return data
  },

  async getSchedules(): Promise<AutomationSchedule[]> {
    const { data } = await apiClient.get('/automation/schedules')
    return data
  },

  async createSchedule(schedule: Partial<AutomationSchedule>): Promise<AutomationSchedule> {
    const { data } = await apiClient.post('/automation/schedules', schedule)
    return data
  },

  async deleteContent(contentId: string): Promise<void> {
    await apiClient.delete(`/automation/content/${contentId}`)
  },
}
