'use client'

import { useState, useEffect, useCallback } from 'react'
import { documentService } from '@/services/document.service'
import type { Document } from '@/types/document'
import toast from 'react-hot-toast'

export function useDocuments() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true)
    try {
      const response = await documentService.list()
      setDocuments(response.documents)
    } catch {
      toast.error('Dokümanlar yüklenemedi')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const uploadDocument = useCallback(async (file: File) => {
    setIsUploading(true)
    try {
      const response = await documentService.upload(file)
      setDocuments((prev) => [response.document, ...prev])
      toast.success(`${file.name} yüklendi`)
      return response.document
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

  useEffect(() => {
    fetchDocuments()
  }, [fetchDocuments])

  return { documents, isLoading, isUploading, uploadDocument, deleteDocument, refetch: fetchDocuments }
}
