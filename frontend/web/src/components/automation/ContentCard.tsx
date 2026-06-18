'use client'

import { useRef, useState } from 'react'
import { PlayCircle, Camera, Video, Check, X, Calendar, Trash2, Play, Square, ChevronDown, ChevronUp, FileText, AlertCircle, Loader2, Pencil, RefreshCw, Archive } from 'lucide-react'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import type { ContentPiece, ContentStatus, ContentPlatform } from '@/types/automation'
import { CONTENT_STATUS_LABELS, PLATFORM_LABELS } from '@/lib/constants'
import { clsx } from 'clsx'

const platformIcons: Record<ContentPlatform, React.ReactNode> = {
  youtube: <PlayCircle size={14} className="text-red-400" />,
  instagram: <Camera size={14} className="text-pink-400" />,
  tiktok: <Video size={14} className="text-cyan-400" />,
  youtube_shorts: <PlayCircle size={14} className="text-red-400" />,
}

const statusVariant: Record<ContentStatus, 'success' | 'warning' | 'error' | 'info' | 'default' | 'purple'> = {
  draft: 'default',
  generating: 'default',
  pending_approval: 'warning',
  approved: 'info',
  rejected: 'error',
  scheduled: 'purple',
  published: 'success',
  failed: 'error',
  error: 'error',
  corrupted: 'error',
  archived: 'default',
}

interface ContentCardProps {
  content: ContentPiece
  onApprove: (id: string) => void
  onReject: (id: string) => void
  onPublish: (id: string) => void
  onDelete: (id: string) => void
  onEdit: (id: string, title: string) => void
  onRetry: (id: string) => void
  onArchive: (id: string) => void
}

export default function ContentCard({ content, onApprove, onReject, onPublish, onDelete, onEdit, onRetry, onArchive }: ContentCardProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [scriptOpen, setScriptOpen] = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const hasVideo = !!(content.video_url && content.video_url.startsWith('http'))
  const hasImage = !!(content.image_url && content.image_url.startsWith('http'))
  const hasAudio = !!content.audio_base64 && !hasVideo
  const hasScript = !!(content.script || content.description)
  const scriptText = content.script || content.description || ''
  const isGenerating = content.status === 'generating'
  const isError = content.status === 'error' || content.status === 'failed' || content.status === 'corrupted'
  const isPending = content.status === 'pending_approval'
  const isApproved = content.status === 'approved'
  const isRetryable = ['error', 'failed', 'corrupted', 'rejected'].includes(content.status)
  const isArchived = content.status === 'archived'

  const handlePlayPause = () => {
    if (!content.audio_base64) return
    if (isPlaying) {
      audioRef.current?.pause()
      setIsPlaying(false)
      return
    }
    const audio = new Audio(`data:audio/mp3;base64,${content.audio_base64}`)
    audioRef.current = audio
    audio.onended = () => setIsPlaying(false)
    audio.onerror = () => setIsPlaying(false)
    audio.play().catch(() => setIsPlaying(false))
    setIsPlaying(true)
  }

  return (
    <div className="bg-surface-50 rounded-xl border border-surface-200 hover:border-surface-300 transition-colors overflow-hidden flex flex-col">

      {/* Video player — tam genişlik, kartın üstünde */}
      {hasVideo && (
        <video
          src={content.video_url}
          controls
          preload="metadata"
          className="w-full bg-black"
          style={{ maxHeight: 220 }}
          onError={(e) => { (e.target as HTMLVideoElement).style.display = 'none' }}
        />
      )}
      {!hasVideo && !hasImage && !isGenerating && !isError && (
        <div className="w-full bg-surface-100 flex items-center justify-center text-xs text-gray-600 py-5 border-b border-surface-200">
          Video dosyası henüz üretilmedi
        </div>
      )}

      {/* Post görseli */}
      {!hasVideo && hasImage && (
        <img
          src={content.image_url}
          alt={content.title}
          className="w-full object-cover"
          style={{ maxHeight: 220 }}
        />
      )}

      <div className="p-4 flex flex-col flex-1">
        {/* Platform + status */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5">
            {platformIcons[content.platform]}
            <span className="text-xs text-gray-500">{PLATFORM_LABELS[content.platform]}</span>
            <span className="text-gray-700">·</span>
            <span className="text-xs text-gray-600">{content.content_type}</span>
          </div>
          <Badge variant={statusVariant[content.status] ?? 'default'} dot>
            {CONTENT_STATUS_LABELS[content.status] ?? content.status}
          </Badge>
        </div>

        <h3 className="text-sm font-semibold text-gray-200 mb-2 line-clamp-2">{content.title}</h3>

        {(content.hashtags ?? []).length > 0 && (
          <div className="flex flex-wrap gap-1 mb-2">
            {content.hashtags.slice(0, 4).map((tag) => (
              <span key={tag} className="text-xs bg-surface-100 text-gray-500 px-1.5 py-0.5 rounded-full">#{tag}</span>
            ))}
          </div>
        )}

        {isGenerating && (
          <div className="flex items-center gap-2 px-3 py-2 bg-surface-100 border border-surface-200 rounded-lg mb-2">
            <Loader2 size={12} className="animate-spin text-brand-400" />
            <span className="text-xs text-gray-400">Üretiliyor, sayfa otomatik yenilenecek...</span>
          </div>
        )}

        {isError && (
          <div className="px-3 py-2.5 bg-red-500/10 border border-red-500/20 rounded-lg mb-2">
            <div className="flex items-center gap-2 mb-1">
              <AlertCircle size={12} className="text-red-400 flex-shrink-0" />
              <span className="text-xs font-semibold text-red-300">Üretim Başarısız</span>
            </div>
            {content.error_detail && (
              <p className="text-xs text-red-400/80 leading-relaxed pl-5 break-words">
                {content.error_detail}
              </p>
            )}
          </div>
        )}

        {/* Ses önizleme — sadece video yoksa */}
        {hasAudio && (
          <button
            onClick={handlePlayPause}
            className={clsx(
              'flex items-center gap-2 w-full px-3 py-1.5 rounded-lg text-xs font-medium transition-colors mb-2',
              isPlaying
                ? 'bg-brand-600/20 text-brand-400 border border-brand-600/30'
                : 'bg-surface-100 text-gray-400 hover:text-gray-200 border border-surface-200'
            )}
          >
            {isPlaying ? <Square size={11} /> : <Play size={11} />}
            {isPlaying ? 'Durdur' : 'Sesi Dinle'}
          </button>
        )}

        {/* Script */}
        {hasScript && (
          <div className="mb-2">
            <button
              onClick={() => setScriptOpen(!scriptOpen)}
              className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-300 transition-colors"
            >
              <FileText size={10} /> Script {scriptOpen ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
            </button>
            {scriptOpen && (
              <div className="mt-1.5 bg-surface-100 border border-surface-200 rounded-lg p-2.5 max-h-36 overflow-y-auto">
                <p className="text-xs text-gray-400 leading-relaxed whitespace-pre-wrap">{scriptText}</p>
              </div>
            )}
          </div>
        )}

        {/* Onay butonları */}
        <div className="mt-auto pt-3 border-t border-surface-200">
          {isPending && (
            <div className="flex gap-2 mb-2">
              <button
                onClick={() => onApprove(content.id)}
                className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg bg-green-600 hover:bg-green-500 text-white text-sm font-semibold transition-colors"
              >
                <Check size={15} /> Onayla
              </button>
              <button
                onClick={() => onReject(content.id)}
                className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white text-sm font-semibold transition-colors"
              >
                <X size={15} /> Reddet
              </button>
            </div>
          )}
          {isApproved && (
            <Button size="sm" variant="primary" className="w-full mb-2" onClick={() => onPublish(content.id)}>
              <Calendar size={13} /> Yayınla
            </Button>
          )}
          {isRetryable && (
            <button
              onClick={() => onRetry(content.id)}
              className="flex items-center justify-center gap-1.5 w-full py-1.5 mb-2 rounded-lg bg-orange-500/10 hover:bg-orange-500/20 border border-orange-500/30 text-orange-400 text-xs font-semibold transition-colors"
            >
              <RefreshCw size={12} /> Yeniden Üret
            </button>
          )}
          <div className="flex items-center gap-3">
            {!isGenerating && !isArchived && (
              <button
                onClick={() => onEdit(content.id, content.title)}
                className="flex items-center gap-1 text-xs text-gray-500 hover:text-brand-400 transition-colors"
              >
                <Pencil size={12} /> Düzenle
              </button>
            )}
            {!isArchived && !isError && !isGenerating && (
              <button
                onClick={() => onArchive(content.id)}
                className="flex items-center gap-1 text-xs text-gray-600 hover:text-yellow-400 transition-colors"
              >
                <Archive size={12} /> Arşivle
              </button>
            )}
            <button
              onClick={() => onDelete(content.id)}
              className="flex items-center gap-1 text-xs text-gray-600 hover:text-red-400 transition-colors ml-auto"
            >
              <Trash2 size={12} /> Sil
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
