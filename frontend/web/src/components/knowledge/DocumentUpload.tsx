'use client'

import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText } from 'lucide-react'
import { clsx } from 'clsx'
import { MAX_FILE_SIZE_MB } from '@/lib/constants'

interface DocumentUploadProps {
  onUpload: (file: File) => Promise<unknown>
  uploadingCount?: number
}

export default function DocumentUpload({ onUpload, uploadingCount = 0 }: DocumentUploadProps) {
  const isUploading = uploadingCount > 0
  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      // Max 2 eş zamanlı yükleme — embedding rate limit koruması
      const CONCURRENCY = 2
      const queue = [...acceptedFiles]
      const workers = Array.from({ length: Math.min(CONCURRENCY, queue.length) }, async () => {
        while (queue.length > 0) {
          const file = queue.shift()
          if (file) await onUpload(file)
        }
      })
      await Promise.all(workers)
    },
    [onUpload]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxSize: MAX_FILE_SIZE_MB * 1024 * 1024,
    multiple: true,
  })

  return (
    <div
      {...getRootProps()}
      className={clsx(
        'border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-200',
        isDragActive
          ? 'border-brand-500 bg-brand-600/10'
          : 'border-surface-200 hover:border-surface-300 hover:bg-surface-50/50',
        isUploading && 'opacity-60 cursor-not-allowed'
      )}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center gap-3">
        <div className={clsx('p-4 rounded-full', isDragActive ? 'bg-brand-600/20' : 'bg-surface-100')}>
          {isUploading ? (
            <svg className="animate-spin h-8 w-8 text-brand-400" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : isDragActive ? (
            <Upload size={32} className="text-brand-400" />
          ) : (
            <FileText size={32} className="text-gray-400" />
          )}
        </div>
        <div>
          <p className="text-sm font-medium text-gray-300">
            {isUploading
              ? `${uploadingCount} dosya işleniyor — yeni dosya ekleyebilirsiniz`
              : isDragActive
              ? 'Dosyaları bırakın'
              : 'Dosyaları sürükleyin veya tıklayın'}
          </p>
          <p className="text-xs text-gray-500 mt-1">PDF, Word, TXT — Maks {MAX_FILE_SIZE_MB}MB</p>
        </div>
      </div>
    </div>
  )
}
