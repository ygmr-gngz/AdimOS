'use client'

import { useState, useEffect, useCallback } from 'react'
import { documentService } from '@/services/document.service'
import type { Document, DocumentSourceModule } from '@/types/document'
import toast from 'react-hot-toast'

export function useDocuments(sourceModule?: DocumentSourceModule) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)

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
  }, [])

  const uploadDocument = useCallback(async (file: File) => {
    setIsUploading(true)
    try {
      const doc = await documentService.upload(file)
      setDocuments((prev) => [doc, ...prev])
      toast.success(`${file.name} yüklendi`)
      return doc
    } catch {
      toast.error('Dosya yüklenemedi')
      return null
    } finally {
      setIsUploading(false)
    }
  }, [])

  const deleteDocument = useCallback(async (id: string) => {
    try {
      await documentService.delete(id)
      setDocuments((prev) => prev.filter((d) => d.id !== id))
      toast.success('Doküman silindi')
    } catch {
      toast.error('Doküman silinemedi')
    }
  }, [])

  useEffect(() => { fetchDocuments() }, [fetchDocuments, sourceModule])

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

  return { documents, isLoading, isUploading, uploadDocument, deleteDocument, reindexDocument, refetch: fetchDocuments }
}
