'use client'

import { Youtube, Instagram, Video, Check, X, Calendar, Trash2 } from 'lucide-react'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import type { ContentPiece, ContentStatus, ContentPlatform } from '@/types/automation'
import { CONTENT_STATUS_LABELS, PLATFORM_LABELS } from '@/lib/constants'

const platformIcons: Record<ContentPlatform, React.ReactNode> = {
  youtube: <Youtube size={14} className="text-red-400" />,
  instagram: <Instagram size={14} className="text-pink-400" />,
  tiktok: <Video size={14} className="text-cyan-400" />,
  youtube_shorts: <Youtube size={14} className="text-red-400" />,
}

const statusVariant: Record<ContentStatus, 'success' | 'warning' | 'error' | 'info' | 'default' | 'purple'> = {
  draft: 'default',
  pending_approval: 'warning',
  approved: 'info',
  rejected: 'error',
  scheduled: 'purple',
  published: 'success',
  failed: 'error',
}

interface ContentCardProps {
  content: ContentPiece
  onApprove: (id: string) => void
  onReject: (id: string) => void
  onPublish: (id: string) => void
  onDelete: (id: string) => void
}

export default function ContentCard({ content, onApprove, onReject, onPublish, onDelete }: ContentCardProps) {
  return (
    <div className="bg-surface-50 rounded-xl p-5 border border-surface-200 hover:border-surface-300 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          {platformIcons[content.platform]}
          <span className="text-xs font-medium text-gray-400">{PLATFORM_LABELS[content.platform]}</span>
          <span className="text-gray-600">·</span>
          <span className="text-xs text-gray-500">{content.content_type}</span>
        </div>
        <Badge variant={statusVariant[content.status]} dot>
          {CONTENT_STATUS_LABELS[content.status]}
        </Badge>
      </div>

      <h3 className="text-sm font-semibold text-gray-200 mb-2">{content.title}</h3>

      {content.description && (
        <p className="text-xs text-gray-500 mb-3 line-clamp-2">{content.description}</p>
      )}

      {content.hashtags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {content.hashtags.slice(0, 5).map((tag) => (
            <span key={tag} className="text-xs bg-surface-100 text-gray-500 px-2 py-0.5 rounded-full">
              #{tag}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center gap-2 mt-3 pt-3 border-t border-surface-200">
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
  )
}
