'use client'

import { useState, useEffect, useCallback } from 'react'
import { documentService } from '@/services/document.service'
import type { Document, DocumentSourceModule } from '@/types/document'
import toast from 'react-hot-toast'

export function useDocuments(sourceModule?: DocumentSourceModule) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [uploadingCount, setUploadingCount] = useState(0)

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true)
    try {
      const response = await documentService.list(sourceModule)
      setDocuments(response)
    } catch {
      toast.error('Dokümanlar yüklenemedi')
    } finally {
      setIsLoading(false)
    }
  }, [sourceModule])

  const uploadDocument = useCallback(async (file: File) => {
    const tempId = `temp-${Date.now()}-${Math.random()}`
    const tempDoc: Document = {
      id: tempId,
      user_id: '',
      file_name: file.name,
      file_path: '',
      file_size: file.size,
      mime_type: file.type || 'application/pdf',
      status: 'processing',
      chunk_count: 0,
      source_module: sourceModule ?? 'knowledge_center',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    setDocuments(prev => [tempDoc, ...prev])
    setUploadingCount(c => c + 1)
    try {
      const doc = await documentService.upload(file)
      setDocuments(prev => prev.map(d => d.id === tempId ? doc : d))
      toast.success(`${file.name} yüklendi`)
      return doc
    } catch {
      setDocuments(prev => prev.filter(d => d.id !== tempId))
      toast.error(`${file.name} yüklenemedi`)
      return null
    } finally {
      setUploadingCount(c => c - 1)
    }
  }, [sourceModule])

  const deleteDocument = useCallback(async (id: string) => {
    try {
      await documentService.delete(id)
      setDocuments((prev) => prev.filter((d) => d.id !== id))
      toast.success('Doküman silindi')
    } catch {
      toast.error('Doküman silinemedi')
    }
  }, [])

  useEffect(() => { fetchDocuments() }, [fetchDocuments])

  const reindexDocument = useCallback(async (id: string) => {
    try {
      setDocuments((prev) => prev.map((d) => d.id === id ? { ...d, status: 'processing' as const } : d))
      await documentService.reindex(id)
      toast.success('Yeniden işleme başlatıldı — birkaç dakika sürebilir')
      setTimeout(fetchDocuments, 10000)
    } catch {
      toast.error('Yeniden işleme başlatılamadı')
    }
  }, [fetchDocuments])

  const isUploading = uploadingCount > 0
  return { documents, isLoading, isUploading, uploadingCount, uploadDocument, deleteDocument, reindexDocument, refetch: fetchDocuments }
}
