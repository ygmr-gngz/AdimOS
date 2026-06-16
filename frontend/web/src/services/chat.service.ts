import apiClient from '@/lib/api-client'
import type { ChatRequest, ChatResponse, Conversation, Message } from '@/types/chat'

export const chatService = {
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const { data } = await apiClient.post('/chat', request)
    return data
  },

  async getConversations(): Promise<Conversation[]> {
    const { data } = await apiClient.get('/chat/conversations')
    return data.conversations ?? []
  },

  async getMessages(conversationId: string): Promise<Message[]> {
    const { data } = await apiClient.get(`/chat/conversations/${conversationId}/messages`)
    return (data.messages ?? []).map((m: Message & { sources?: unknown }) => ({
      ...m,
      id: m.id || String(Date.now()),
    }))
  },

  async deleteConversation(conversationId: string): Promise<void> {
    await apiClient.delete(`/chat/conversations/${conversationId}`)
  },
}
