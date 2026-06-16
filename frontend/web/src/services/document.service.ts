import apiClient from '@/lib/api-client'
import type { Document } from '@/types/document'

export const documentService = {
  async upload(file: File): Promise<Document> {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await apiClient.post('/documents', formData)
    return data
  },

  async list(): Promise<Document[]> {
    const { data } = await apiClient.get('/documents')
    return Array.isArray(data) ? data : data.documents ?? []
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
}
