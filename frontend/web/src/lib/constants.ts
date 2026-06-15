export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export const ROUTES = {
  HOME: '/',
  DASHBOARD: '/dashboard',
  KNOWLEDGE: '/knowledge',
  CHAT: '/chat',
  VOICE: '/voice',
  AGENTS: '/agents',
  AUTOMATION: '/automation',
  CRM: '/crm',
  ACADEMY: '/academy',
  SETTINGS: '/settings',
} as const

export const DOCUMENT_STATUS_LABELS: Record<string, string> = {
  uploaded: 'Yüklendi',
  processing: 'İşleniyor',
  indexed: 'Hazır',
  failed: 'Hata',
}

export const AGENT_STATUS_LABELS: Record<string, string> = {
  idle: 'Bekliyor',
  running: 'Çalışıyor',
  completed: 'Tamamlandı',
  failed: 'Hata',
}

export const CONTENT_STATUS_LABELS: Record<string, string> = {
  draft: 'Taslak',
  pending_approval: 'Onay Bekliyor',
  approved: 'Onaylandı',
  rejected: 'Reddedildi',
  scheduled: 'Planlandı',
  published: 'Yayınlandı',
  failed: 'Hata',
}

export const PLATFORM_LABELS: Record<string, string> = {
  youtube: 'YouTube',
  instagram: 'Instagram',
  tiktok: 'TikTok',
  youtube_shorts: 'YouTube Shorts',
}

export const MAX_FILE_SIZE_MB = 50
export const SUPPORTED_FILE_TYPES = ['application/pdf', 'text/plain', 'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
