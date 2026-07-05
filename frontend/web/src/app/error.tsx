'use client'

import { useEffect } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('[Route Error]', error)
  }, [error])

  return (
    <div className="flex items-center justify-center min-h-screen bg-surface">
      <div className="bg-surface-50 border border-red-500/30 rounded-xl p-8 max-w-md w-full text-center mx-4">
        <AlertTriangle className="mx-auto mb-4 text-red-400" size={32} />
        <h2 className="text-base font-semibold text-white mb-2">Sayfa yüklenemedi</h2>
        <p className="text-xs text-gray-500 mb-6 font-mono break-all">
          {error.message?.slice(0, 200) ?? 'Beklenmeyen bir hata oluştu.'}
        </p>
        <button
          onClick={reset}
          className="inline-flex items-center gap-2 text-sm text-brand-400 hover:text-brand-300 transition-colors"
        >
          <RefreshCw size={14} />
          Yeniden dene
        </button>
      </div>
    </div>
  )
}
