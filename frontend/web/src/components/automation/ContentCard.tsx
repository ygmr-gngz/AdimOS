'use client'

import { useRef, useState } from 'react'
import { PlayCircle, Camera, Video, Check, X, Calendar, Trash2, Play, Square, ChevronDown, ChevronUp, FileText, AlertCircle, Loader2 } from 'lucide-react'
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
}

interface ContentCardProps {
  content: ContentPiece
  onApprove: (id: string) => void
  onReject: (id: string) => void
  onPublish: (id: string) => void
  onDelete: (id: string) => void
}

export default function ContentCard({ content, onApprove, onReject, onPublish, onDelete }: ContentCardProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [scriptOpen, setScriptOpen] = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const hasAudio = !!content.audio_base64
  const hasScript = !!(content.script || content.description)
  const scriptText = content.script || content.description || ''
  const isGenerating = content.status === 'generating'
  const isError = content.status === 'error' || content.status === 'failed'
  const hasVideo = !!(content.video_url && content.video_url.startsWith('http'))
  const hasImage = !!(content.image_url && content.image_url.startsWith('http'))

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
    <div className="bg-surface-50 rounded-xl border border-surface-200 hover:border-surface-300 transition-colors overflow-hidden">
      <div className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            {platformIcons[content.platform]}
            <span className="text-xs font-medium text-gray-400">{PLATFORM_LABELS[content.platform]}</span>
            <span className="text-gray-600">·</span>
            <span className="text-xs text-gray-500">{content.content_type}</span>
          </div>
          <Badge variant={statusVariant[content.status] ?? 'default'} dot>
            {CONTENT_STATUS_LABELS[content.status] ?? content.status}
          </Badge>
        </div>

        <h3 className="text-sm font-semibold text-gray-200 mb-2">{content.title}</h3>

        {(content.hashtags ?? []).length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {content.hashtags.slice(0, 5).map((tag) => (
              <span key={tag} className="text-xs bg-surface-100 text-gray-500 px-2 py-0.5 rounded-full">
                #{tag}
              </span>
            ))}
          </div>
        )}

        {isGenerating && (
          <div className="flex items-center gap-2 px-3 py-2 bg-surface-100 border border-surface-200 rounded-lg mb-3">
            <Loader2 size={12} className="animate-spin text-brand-400" />
            <span className="text-xs text-gray-400">İçerik üretiliyor, sayfayı yenileyin...</span>
          </div>
        )}

        {isError && (
          <div className="flex items-center gap-2 px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg mb-3">
            <AlertCircle size={12} className="text-red-400" />
            <span className="text-xs text-red-300">Üretim başarısız. Yeniden deneyin.</span>
          </div>
        )}

        {hasVideo && (
          <div className="mb-3">
            <video
              src={content.video_url}
              controls
              className="w-full rounded-lg max-h-40 bg-black"
            />
          </div>
        )}

        {hasImage && (
          <div className="mb-3">
            <img
              src={content.image_url}
              alt={content.title}
              className="w-full rounded-lg max-h-48 object-cover"
            />
          </div>
        )}

        {hasAudio && (
          <button
            onClick={handlePlayPause}
            className={clsx(
              'flex items-center gap-2 w-full px-3 py-2 rounded-lg text-xs font-medium transition-colors mb-3',
              isPlaying
                ? 'bg-brand-600/20 text-brand-400 border border-brand-600/30'
                : 'bg-surface-100 text-gray-400 hover:text-gray-200 border border-surface-200 hover:border-surface-300'
            )}
          >
            {isPlaying ? <Square size={12} /> : <Play size={12} />}
            {isPlaying ? 'Durdur' : '▶ Sesi Dinle'}
          </button>
        )}

        {hasScript && (
          <div className="mb-3">
            <button
              onClick={() => setScriptOpen(!scriptOpen)}
              className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-300 transition-colors"
            >
              <FileText size={11} />
              Script
              {scriptOpen ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
            </button>
            {scriptOpen && (
              <div className="mt-2 bg-surface-100 border border-surface-200 rounded-lg p-3 max-h-48 overflow-y-auto">
                <p className="text-xs text-gray-400 leading-relaxed whitespace-pre-wrap">{scriptText}</p>
              </div>
            )}
          </div>
        )}

        <div className="flex items-center gap-2 pt-3 border-t border-surface-200">
          {content.status === 'pending_approval' && (
            <>
              <Button size="sm" variant="primary" onClick={() => onApprove(content.id)}>
                <Check size={13} /> Onayla
              </Button>
              <Button size="sm" variant="danger" onClick={() => onReject(content.id)}>
                <X size={13} /> Reddet
              </Button>
            </>
          )}
          {content.status === 'approved' && (
            <Button size="sm" variant="primary" onClick={() => onPublish(content.id)}>
              <Calendar size={13} /> Yayınla
            </Button>
          )}
          <button
            onClick={() => onDelete(content.id)}
            className="ml-auto p-1.5 rounded-lg hover:bg-red-500/10 text-gray-600 hover:text-red-400 transition-colors"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>
    </div>
  )
}
