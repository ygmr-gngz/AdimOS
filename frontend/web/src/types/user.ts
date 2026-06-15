export interface User {
  id: string
  email: string
  full_name?: string
  avatar_url?: string
  created_at: string
}

export interface UserProfile {
  id: string
  user_id: string
  full_name: string
  company?: string
  role: 'admin' | 'user'
  settings: UserSettings
  created_at: string
  updated_at: string
}

export interface UserSettings {
  language: 'tr' | 'en'
  voice_enabled: boolean
  tts_voice: string
  notifications_enabled: boolean
  theme: 'dark' | 'light'
}
