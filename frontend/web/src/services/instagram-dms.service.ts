import apiClient from '@/lib/api-client'

export interface InstagramConversation {
  id: string
  instagram_user_id: string
  current_step: string
  last_message_at: string
  source: string
  interest: string | null
  crm_lead_id: string | null
  created_at: string
}

export interface InstagramMessage {
  id: string
  message_id: string
  sender_id: string
  recipient_id: string
  message_text: string
  direction: 'inbound' | 'outbound'
  created_at: string
}

export interface TestDmResult {
  sender_id: string
  message_text: string
  matched_flow: string | null
  reply: string
  crm_status: string | null
  crm_interest: string | null
  would_create_crm_lead: boolean
}

export const instagramDmsService = {
  async listConversations(): Promise<InstagramConversation[]> {
    const { data } = await apiClient.get('/meta/conversations')
    return data ?? []
  },

  async getMessages(instagramUserId: string): Promise<InstagramMessage[]> {
    const { data } = await apiClient.get(`/meta/messages/${instagramUserId}`)
    return data ?? []
  },

  async sendMessage(instagramUserId: string, text: string): Promise<void> {
    await apiClient.post('/meta/send', { instagram_user_id: instagramUserId, text })
  },

  async testDmFlow(senderId: string, messageText: string): Promise<TestDmResult> {
    const { data } = await apiClient.post('/meta/test-dm-flow', {
      sender_id: senderId,
      message_text: messageText,
    })
    return data
  },
}
