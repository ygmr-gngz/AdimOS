'use client'

import { X, Trash2, CheckCircle, AlertTriangle, Loader2 } from 'lucide-react'

interface CleanupReport {
  deleted_failed: number
  deleted_stuck: number
  deleted_corrupted: number
  deleted_orphan: number
  storage_cleaned: number
  total_deleted: number
}

interface Props {
  isOpen: boolean
  onClose: () => void
  report: CleanupReport | null
  loading: boolean
}

const LINE_LABELS: { key: keyof CleanupReport; label: string; icon?: boolean }[] = [
  { key: 'deleted_failed', label: 'Başarısız içerik silindi' },
  { key: 'deleted_stuck', label: 'Takılı render kaldırıldı' },
  { key: 'deleted_corrupted', label: 'Bozuk kayıt temizlendi' },
  { key: 'deleted_orphan', label: 'Yetim (URL\'siz) kayıt silindi' },
  { key: 'storage_cleaned', label: 'Storage dosyası silindi' },
]

export default function CleanupReportModal({ isOpen, onClose, report, loading }: Props) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-md bg-surface-50 border border-surface-200 rounded-2xl shadow-2xl overflow-hidden">

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-surface-200">
          <div className="flex items-center gap-2">
            <Trash2 size={16} className="text-orange-400" />
            <p className="text-sm font-semibold text-white">Sistem Temizliği</p>
          </div>
          <button onClick={onClose} className="p-1.5 text-gray-500 hover:text-gray-300 transition-colors">
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-8 gap-3">
              <Loader2 size={28} className="text-brand-400 animate-spin" />
              <p className="text-sm text-gray-400">Sistem temizleniyor...</p>
              <p className="text-xs text-gray-600">Bu işlem birkaç saniye sürebilir</p>
            </div>
          ) : report ? (
            <div className="space-y-4">
              {/* Özet */}
              <div className={`rounded-xl p-4 border text-center ${
                report.total_deleted > 0
                  ? 'bg-green-500/10 border-green-500/20'
                  : 'bg-surface-100 border-surface-200'
              }`}>
                <p className="text-2xl font-bold text-white">{report.total_deleted}</p>
                <p className="text-sm text-gray-400 mt-0.5">
                  {report.total_deleted > 0 ? 'kayıt temizlendi' : 'Temizlenecek kayıt bulunamadı'}
                </p>
              </div>

              {/* Detay */}
              <div className="space-y-2">
                {LINE_LABELS.map(({ key, label }) => {
                  const val = report[key] ?? 0
                  return (
                    <div
                      key={key}
                      className={`flex items-center justify-between p-3 rounded-lg border ${
                        val > 0
                          ? 'bg-orange-500/5 border-orange-500/20'
                          : 'bg-surface-100 border-surface-200 opacity-50'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {val > 0
                          ? <CheckCircle size={13} className="text-green-400" />
                          : <div className="w-3 h-3 rounded-full border border-gray-600" />
                        }
                        <span className="text-xs text-gray-300">{label}</span>
                      </div>
                      <span className={`text-sm font-bold ${val > 0 ? 'text-orange-400' : 'text-gray-600'}`}>
                        {val}
                      </span>
                    </div>
                  )
                })}
              </div>

              {report.total_deleted === 0 && (
                <div className="flex items-center gap-2 p-3 bg-surface-100 rounded-xl border border-surface-200">
                  <CheckCircle size={14} className="text-green-400 shrink-0" />
                  <p className="text-xs text-gray-400">Sistem zaten temiz. Temizlenecek kayıt yok.</p>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2 p-3 bg-red-500/10 rounded-xl border border-red-500/20">
              <AlertTriangle size={14} className="text-red-400 shrink-0" />
              <p className="text-xs text-red-400">Temizlik başarısız oldu. Tekrar deneyin.</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 pb-5">
          <button
            onClick={onClose}
            className="w-full py-2.5 bg-surface-100 hover:bg-surface-200 border border-surface-300 text-gray-300 text-sm font-medium rounded-xl transition-colors"
          >
            Kapat
          </button>
        </div>
      </div>
    </div>
  )
}
