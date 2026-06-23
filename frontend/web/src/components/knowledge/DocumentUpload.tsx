'use client'

import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText } from 'lucide-react'
import { clsx } from 'clsx'
import { SUPPORTED_FILE_TYPES, MAX_FILE_SIZE_MB } from '@/lib/constants'

interface DocumentUploadProps {
  onUpload: (file: File) => Promise<unknown>
  isUploading: boolean
}

export default function DocumentUpload({ onUpload, isUploading }: DocumentUploadProps) {
  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      for (const file of acceptedFiles) {
        await onUpload(file)
      }
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
    disabled: isUploading,
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
              ? 'Yükleniyor...'
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
