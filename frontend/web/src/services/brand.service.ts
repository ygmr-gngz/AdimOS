import apiClient from '@/lib/api-client'

export interface BrandSettings {
  id?: string
  logo_url?: string | null
  watermark_enabled: boolean
  watermark_opacity: number
  watermark_position: 'center' | 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left'
  watermark_size: number
  logo_corner_position: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left'
  updated_at?: string
}

export const brandService = {
  async getSettings(): Promise<BrandSettings> {
    const { data } = await apiClient.get('/brand/settings')
    return data
  },

  async updateSettings(updates: Partial<BrandSettings>): Promise<BrandSettings> {
    const { data } = await apiClient.put('/brand/settings', updates)
    return data
  },

  async uploadLogo(file: File): Promise<{ logo_url: string; settings: BrandSettings }> {
    const form = new FormData()
    form.append('file', file)
    const { data } = await apiClient.post('/brand/logo', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  async deleteLogo(): Promise<void> {
    await apiClient.delete('/brand/logo')
  },
}

export const POSITION_LABELS: Record<string, string> = {
  'center': 'Merkez filigran',
  'top-right': 'Sağ üst',
  'top-left': 'Sol üst',
  'bottom-right': 'Sağ alt',
  'bottom-left': 'Sol alt',
}
