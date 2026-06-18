import apiClient from '@/lib/api-client'

export interface Notification {
  id: string
  type: string
  title: string
  body: string
  is_read: boolean
  created_at: string
}

export const notificationsService = {
  async list(): Promise<{ notifications: Notification[]; unread_count: number }> {
    const { data } = await apiClient.get('/notifications')
    return data
  },

  async markRead(id: string): Promise<void> {
    await apiClient.patch(`/notifications/${id}/read`)
  },

  async markAllRead(): Promise<void> {
    await apiClient.patch('/notifications/read-all')
  },

  async clearRead(): Promise<void> {
    await apiClient.delete('/notifications')
  },
}
