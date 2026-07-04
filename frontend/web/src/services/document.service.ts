import apiClient from '@/lib/api-client'
import type { Document, DocumentSourceModule } from '@/types/document'

export interface SyncSgsResult {
  synced: number
  already_exists: number
  errors: number
  total_analyses: number
}

export const documentService = {
  async upload(file: File): Promise<Document> {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await apiClient.post('/documents', formData)
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
