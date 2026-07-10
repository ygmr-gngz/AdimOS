import apiClient from '@/lib/api-client'
import type { Document, DocumentSourceModule } from '@/types/document'

export interface SyncSgsResult {
  synced: number
  already_exists: number
  errors: number
  total_analyses: number
}

export interface UploadUrlResult {
  doc_id: string
  signed_url: string
  path: string
  file_name: string
}

export const documentService = {
  /** Eski yol — artık kullanılmıyor; büyük dosyalar için uploadDirect kullan */
  async upload(file: File, sourceModule?: DocumentSourceModule, excludeFromSgs?: boolean): Promise<Document> {
    const formData = new FormData()
    formData.append('file', file)
    if (sourceModule) formData.append('source_module', sourceModule)
    if (excludeFromSgs) formData.append('exclude_from_sgs', 'true')
    const { data } = await apiClient.post('/documents', formData)
    return data
  },

  /** Doğrudan-storage yükleme: dosya API gövdesinden geçmez */
  async getUploadUrl(
    file: File,
    sourceModule?: DocumentSourceModule,
    excludeFromSgs?: boolean,
  ): Promise<UploadUrlResult> {
    const params: Record<string, string | number | boolean> = {
      file_name: file.name,
      file_size: file.size,
      source_module: sourceModule ?? 'knowledge_center',
    }
    if (excludeFromSgs) params.exclude_from_sgs = true
    const { data } = await apiClient.get('/documents/upload-url', { params })
    return data
  },

  async uploadToSignedUrl(
    signedUrl: string,
    file: File,
    onProgress?: (pct: number) => void,
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      if (onProgress) {
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100))
        }
      }
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) resolve()
        else reject(new Error(`Storage yükleme hatası: HTTP ${xhr.status} — ${xhr.responseText.slice(0, 200)}`))
      }
      xhr.onerror = () => reject(new Error('Ağ hatası — bağlantıyı kontrol edin'))
      xhr.ontimeout = () => reject(new Error('Yükleme zaman aşımına uğradı'))
      xhr.timeout = 15 * 60 * 1000  // 15 dakika
      xhr.open('PUT', signedUrl)
      xhr.setRequestHeader('Content-Type', file.type || 'application/pdf')
      xhr.send(file)
    })
  },

  async registerUpload(docId: string, excludeFromSgs?: boolean): Promise<{ doc_id: string; status: string }> {
    const params = excludeFromSgs ? { exclude_from_sgs: true } : {}
    const { data } = await apiClient.post(`/documents/register-upload/${docId}`, null, { params })
    return data
  },

  async list(sourceModule?: DocumentSourceModule): Promise<Document[]> {
    const params = sourceModule ? { source_module: sourceModule } : undefined
    const { data } = await apiClient.get('/documents', { params })
    return Array.isArray(data) ? data : data.documents ?? []
  },

  async syncSgs(): Promise<SyncSgsResult> {
    const { data } = await apiClient.post('/documents/sync-sgs')
    return data
  },

  async getById(id: string): Promise<Document> {
    const { data } = await apiClient.get(`/documents/${id}`)
    return data
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/documents/${id}`)
  },

  async reindex(id: string): Promise<void> {
    await apiClient.post(`/documents/${id}/reindex`)
  },

  async relink(id: string, file: File): Promise<void> {
    const formData = new FormData()
    formData.append('file', file)
    await apiClient.patch(`/documents/${id}/relink`, formData)
  },

  async verifyStorage(): Promise<{ message: string }> {
    const { data } = await apiClient.post('/documents/verify-storage')
    return data
  },
}
