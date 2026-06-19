'use client'

import { useEffect } from 'react'
import { X, Check, X as XIcon, Calendar, Download, PlayCircle } from 'lucide-react'
import type { ContentPiece } from '@/types/automation'
import Badge from '@/components/ui/Badge'
import { CONTENT_STATUS_LABELS } from '@/lib/constants'

interface VideoReviewModalProps {
  content: ContentPiece | null
  onClose: () => void
  onApprove: (id: string) => void
  onReject: (id: string) => void
  onPublish: (id: string) => void
}

export default function VideoReviewModal({
  content, onClose, onApprove, onReject, onPublish
}: VideoReviewModalProps) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  if (!content) return null

  const isPending = content.status === 'pending_approval'
  const isApproved = content.status === 'approved'
  const hasVideo = !!(content.video_url?.startsWith('http'))
  const scriptText = content.script || content.description || ''

  return (
    <div className="fixed inset-0 z-[300] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative w-full max-w-3xl bg-surface-50 rounded-2xl border border-surface-200 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-surface-200 shrink-0">
          <div className="flex items-center gap-2 min-w-0">
            <PlayCircle size={15} className="text-brand-400 shrink-0" />
            <p className="text-sm font-semibold text-gray-200 truncate">{content.title}</p>
            <Badge variant={
              content.status === 'pending_approval' ? 'warning' :
              content.status === 'approved' ? 'info' :
              content.status === 'published' ? 'success' : 'default'
            } dot>
              {CONTENT_STATUS_LABELS[content.status] ?? content.status}
            </Badge>
          </div>
          <button onClick={onClose} className="p-1.5 text-gray-500 hover:text-gray-300 transition-colors shrink-0">
            <X size={18} />
          </button>
        </div>

        {/* Video */}
        <div className="bg-black flex-shrink-0">
          {hasVideo ? (
            <video
              src={content.video_url}
              controls
              autoPlay
              className="w-full"
              style={{ maxHeight: '50vh' }}
            />
          ) : content.image_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={content.image_url}
              alt={content.title}
              className="w-full object-contain"
              style={{ maxHeight: '50vh' }}
            />
          ) : (
            <div className="w-full h-40 flex items-center justify-center text-gray-600 text-sm">
              Medya dosyası yok
            </div>
          )}
        </div>

        {/* Script */}
        {scriptText && (
          <div className="px-5 py-3 border-t border-surface-200 overflow-y-auto" style={{ maxHeight: 150 }}>
            <p className="text-xs font-semibold text-gray-500 mb-1">Script / Açıklama</p>
            <p className="text-xs text-gray-400 leading-relaxed whitespace-pre-wrap">{scriptText}</p>
          </div>
        )}

        {/* Aksiyon butonları */}
        <div className="px-5 py-4 border-t border-surface-200 shrink-0">
          <div className="flex flex-wrap gap-2">
            {isPending && (
              <>
                <button
                  onClick={() => { onApprove(content.id); onClose() }}
                  className="flex-1 min-w-[120px] flex items-center justify-center gap-2 py-2.5 rounded-xl bg-green-600 hover:bg-green-500 text-white text-sm font-semibold transition-colors"
                >
                  <Check size={16} /> Onayla
                </button>
                <button
                  onClick={() => { onReject(content.id); onClose() }}
                  className="flex-1 min-w-[120px] flex items-center justify-center gap-2 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-semibold transition-colors"
                >
                  <XIcon size={16} /> Reddet
                </button>
              </>
            )}
            {isApproved && (
              <button
                onClick={() => { onPublish(content.id); onClose() }}
                className="flex-1 min-w-[120px] flex items-center justify-center gap-2 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-sm font-semibold transition-colors"
              >
                <Calendar size={16} /> Instagram&apos;a Yayınla
              </button>
            )}
            {hasVideo && (
              <a
                href={content.video_url}
                download
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-surface-100 border border-surface-200 text-gray-400 hover:text-gray-200 text-sm font-medium transition-colors"
              >
                <Download size={15} /> İndir
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
