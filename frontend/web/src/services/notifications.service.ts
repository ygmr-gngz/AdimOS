import apiClient from '@/lib/api-client'

export interface Notification {
  id: string
  type: string
  title: string
  body?: string
  message?: string
  is_read: boolean
  status: 'info' | 'success' | 'warning' | 'error'
  priority: 'low' | 'normal' | 'high' | 'critical'
  details?: Record<string, unknown>
  related_entity_type?: string
  related_entity_id?: string
  action_url?: string
  created_at: string
}

export const notificationsService = {
  async list(limit = 80): Promise<{ notifications: Notification[]; unread_count: number }> {
    const { data } = await apiClient.get(`/notifications?limit=${limit}`)
    return data
  },

  async unreadCount(): Promise<number> {
    const { data } = await apiClient.get('/notifications/unread-count')
    return data.unread_count ?? 0
  },

  async markRead(id: string): Promise<void> {
    await apiClient.patch(`/notifications/${id}/read`)
  },

  async markAllRead(): Promise<void> {
    await apiClient.patch('/notifications/read-all')
  },

  async deleteOne(id: string): Promise<void> {
    await apiClient.delete(`/notifications/${id}`)
  },

  async clearRead(): Promise<void> {
    await apiClient.delete('/notifications/clear-read')
  },
}

// Türe göre görsel ayarlar
export type NotifColor = 'green' | 'red' | 'yellow' | 'blue' | 'purple' | 'gray'

export function getNotifColor(n: Notification): NotifColor {
  if (n.status === 'error' || n.type.includes('fail') || n.type.includes('error')) return 'red'
  if (n.status === 'success') return 'green'
  if (n.status === 'warning' || n.type === 'followup_due') return 'yellow'
  if (n.type.startsWith('agent') || n.type.startsWith('ceo')) return 'purple'
  if (n.type.startsWith('sgs') || n.type === 'question_range_saved') return 'blue'
  if (n.type.startsWith('content')) return 'green'
  if (n.type.startsWith('document')) return 'yellow'
  if (n.type.startsWith('lead')) return 'green'
  return 'gray'
}

export type FilterKey = 'all' | 'unread' | 'error' | 'content' | 'document' | 'crm' | 'agent' | 'sgs'

export const FILTER_LABELS: Record<FilterKey, string> = {
  all: 'Tümü',
  unread: 'Okunmamış',
  error: 'Hatalar',
  content: 'İçerikler',
  document: 'Belgeler',
  crm: 'CRM',
  agent: 'Agentlar',
  sgs: 'SGS',
}

export function filterNotif(n: Notification, key: FilterKey): boolean {
  switch (key) {
    case 'unread':  return !n.is_read
    case 'error':   return n.status === 'error' || n.type.includes('fail') || n.type.includes('error')
    case 'content': return n.type.startsWith('content')
    case 'document':return n.type.startsWith('document')
    case 'crm':     return n.type.startsWith('lead') || n.type === 'followup_due'
    case 'agent':   return n.type.startsWith('agent') || n.type.startsWith('ceo')
    case 'sgs':     return n.type.startsWith('sgs') || n.type === 'question_range_saved'
    default:        return true
  }
}

export function groupByDate(items: Notification[]): { label: string; items: Notification[] }[] {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today.getTime() - 86400000)
  const weekAgo = new Date(today.getTime() - 6 * 86400000)

  const groups: Record<string, Notification[]> = {
    'Bugün': [], 'Dün': [], 'Bu Hafta': [], 'Daha Eski': []
  }

  for (const n of items) {
    const d = new Date(n.created_at)
    if (d >= today) groups['Bugün'].push(n)
    else if (d >= yesterday) groups['Dün'].push(n)
    else if (d >= weekAgo) groups['Bu Hafta'].push(n)
    else groups['Daha Eski'].push(n)
  }

  return Object.entries(groups)
    .filter(([, v]) => v.length > 0)
    .map(([label, items]) => ({ label, items }))
}

export function timeAgo(iso: string): string {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000
  if (diff < 60) return 'az önce'
  if (diff < 3600) return `${Math.floor(diff / 60)} dk önce`
  if (diff < 86400) return `${Math.floor(diff / 3600)} sa önce`
  return `${Math.floor(diff / 86400)} gün önce`
}
