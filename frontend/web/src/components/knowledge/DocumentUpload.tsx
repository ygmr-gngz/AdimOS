'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, CheckCircle2 } from 'lucide-react'
import { clsx } from 'clsx'
import { MAX_FILE_SIZE_MB } from '@/lib/constants'

interface DocumentUploadProps {
  onUpload: (file: File, onProgress?: (pct: number) => void) => Promise<unknown>
  uploadingCount?: number
}

interface FileProgress {
  name: string
  pct: number
  done: boolean
}

export default function DocumentUpload({ onUpload, uploadingCount = 0 }: DocumentUploadProps) {
  const [fileProgress, setFileProgress] = useState<Record<string, FileProgress>>({})
  const isUploading = uploadingCount > 0

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const CONCURRENCY = 2
      const queue = [...acceptedFiles]

      const workers = Array.from({ length: Math.min(CONCURRENCY, queue.length) }, async () => {
        while (queue.length > 0) {
          const file = queue.shift()
          if (!file) continue

          const key = `${file.name}-${file.size}`
          setFileProgress(prev => ({ ...prev, [key]: { name: file.name, pct: 0, done: false } }))

          await onUpload(file, (pct) => {
            setFileProgress(prev => ({ ...prev, [key]: { name: file.name, pct, done: pct >= 100 } }))
          })

          setFileProgress(prev => ({ ...prev, [key]: { name: file.name, pct: 100, done: true } }))
          setTimeout(() => {
            setFileProgress(prev => {
              const next = { ...prev }
              delete next[key]
              return next
            })
          }, 2000)
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
    disabled: isUploading,
  })

  const progressItems = Object.values(fileProgress)

  return (
    <div className="space-y-2">
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
                ? `${uploadingCount} dosya yükleniyor`
                : isDragActive
                ? 'Dosyaları bırakın'
                : 'Dosyaları sürükleyin veya tıklayın'}
            </p>
            <p className="text-xs text-gray-500 mt-1">PDF, Word, TXT — Maks {MAX_FILE_SIZE_MB} MB</p>
          </div>
        </div>
      </div>

      {/* İlerleme çubukları */}
      {progressItems.length > 0 && (
        <div className="space-y-1.5">
          {progressItems.map((fp) => (
            <div key={fp.name} className="bg-surface-50 rounded-lg px-3 py-2 border border-surface-200">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-gray-400 truncate max-w-[80%]">{fp.name}</span>
                <span className="text-xs text-gray-500 flex-shrink-0 ml-2">
                  {fp.done ? (
                    <CheckCircle2 size={12} className="text-emerald-400" />
                  ) : (
                    `${fp.pct}%`
                  )}
                </span>
              </div>
              <div className="h-1 bg-surface-200 rounded-full overflow-hidden">
                <div
                  className={clsx(
                    'h-full rounded-full transition-all duration-300',
                    fp.done ? 'bg-emerald-500' : 'bg-brand-500'
                  )}
                  style={{ width: `${fp.pct}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
