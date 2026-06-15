import apiClient from '@/lib/api-client'
import type { ChatRequest, ChatResponse } from '@/types/chat'

export const chatService = {
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const { data } = await apiClient.post('/chat', request)
    return data
  },
}
