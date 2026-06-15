import apiClient from '@/lib/api-client'
import type { Document, ListDocumentsResponse, UploadDocumentResponse } from '@/types/document'

export const documentService = {
  async upload(file: File): Promise<UploadDocumentResponse> {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await apiClient.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  async list(): Promise<ListDocumentsResponse> {
    const { data } = await apiClient.get('/documents')
    return data
  },

  async getById(id: string): Promise<Document> {
    const { data } = await apiClient.get(`/documents/${id}`)
    return data
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/documents/${id}`)
  },
}
