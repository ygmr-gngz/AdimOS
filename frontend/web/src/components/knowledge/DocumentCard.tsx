import { FileText, Trash2, CheckCircle2, Clock, AlertCircle, Loader2, RefreshCw, GraduationCap } from 'lucide-react'
import Badge from '@/components/ui/Badge'
import type { Document, DocumentStatus, DocumentSourceModule } from '@/types/document'
import { DOCUMENT_STATUS_LABELS } from '@/lib/constants'

const SOURCE_MODULE_CONFIG: Record<DocumentSourceModule, { label: string; className: string }> = {
  knowledge_center: { label: 'Bilgi Merkezi', className: 'text-blue-400 bg-blue-500/10' },
  sgs_academy: { label: 'SGS Akademi', className: 'text-brand-400 bg-brand-500/10' },
  crm: { label: 'CRM', className: 'text-purple-400 bg-purple-500/10' },
  content_automation: { label: 'Otomasyon', className: 'text-orange-400 bg-orange-500/10' },
}

const statusConfig: Record<DocumentStatus, { variant: 'success' | 'warning' | 'error' | 'info'; icon: React.ReactNode }> = {
  uploaded: { variant: 'info', icon: <Clock size={12} /> },
  processing: { variant: 'warning', icon: <Loader2 size={12} className="animate-spin" /> },
  indexed: { variant: 'success', icon: <CheckCircle2 size={12} /> },
  failed: { variant: 'error', icon: <AlertCircle size={12} /> },
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

interface DocumentCardProps {
  document: Document
  onDelete: (id: string) => void
  onReindex?: (id: string) => void
}

export default function DocumentCard({ document: doc, onDelete, onReindex }: DocumentCardProps) {
  const config = statusConfig[doc.status]
  const canReindex = doc.status === 'failed' || doc.status === 'uploaded'

  return (
    <div className="flex items-center gap-4 p-4 bg-surface-50 rounded-lg border border-surface-200 hover:border-surface-300 transition-colors group">
      <div className="p-2 bg-surface-100 rounded-lg flex-shrink-0">
        <FileText size={18} className="text-gray-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-200 truncate">{doc.file_name}</p>
        <p className="text-xs text-gray-500 mt-0.5">
          {formatFileSize(doc.file_size)} · {doc.chunk_count ?? 0} bölüm · {new Date(doc.created_at).toLocaleDateString('tr-TR')}
        </p>
      </div>
      {doc.source_module && doc.source_module !== 'knowledge_center' && (() => {
        const src = SOURCE_MODULE_CONFIG[doc.source_module]
        return src ? (
          <span className={`hidden sm:flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${src.className}`}>
            <GraduationCap size={11} />
            {src.label}
          </span>
        ) : null
      })()}
      <Badge variant={config.variant}>
        {config.icon}
        {DOCUMENT_STATUS_LABELS[doc.status]}
      </Badge>
      {canReindex && onReindex && (
        <button
          onClick={() => onReindex(doc.id)}
          title="Yeniden işle"
          className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-brand-500/20 text-gray-600 hover:text-brand-400 transition-all"
        >
          <RefreshCw size={15} />
        </button>
      )}
      <button
        onClick={() => onDelete(doc.id)}
        title="Sil"
        className={`p-1.5 rounded-lg hover:bg-red-500/20 hover:text-red-400 transition-all ${
          doc.status === 'failed'
            ? 'text-red-500 opacity-100'
            : 'opacity-0 group-hover:opacity-100 text-gray-600'
        }`}
      >
        <Trash2 size={15} />
      </button>
    </div>
  )
}
