'use client'

import { useState, useEffect, useCallback } from 'react'
import AppShell from '@/components/layout/AppShell'
import ContentCard from '@/components/automation/ContentCard'
import GenerateContentModal from '@/components/automation/GenerateContentModal'
import Button from '@/components/ui/Button'
import { automationService } from '@/services/automation.service'
import type { ContentPiece, GenerateContentRequest } from '@/types/automation'
import { Plus, Video, Filter } from 'lucide-react'
import toast from 'react-hot-toast'
import { clsx } from 'clsx'

const FILTERS = [
  { value: '', label: 'Tümü' },
  { value: 'pending_approval', label: 'Onay Bekleyen' },
  { value: 'approved', label: 'Onaylanan' },
  { value: 'published', label: 'Yayınlanan' },
  { value: 'draft', label: 'Taslak' },
]

export default function AutomationPage() {
  const [content, setContent] = useState<ContentPiece[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [filter, setFilter] = useState('')

  const fetchContent = useCallback(async () => {
    try {
      const data = await automationService.listContent(filter || undefined)
      setContent(data)
    } catch {
      toast.error('İçerikler yüklenemedi')
    } finally {
      setIsLoading(false)
    }
  }, [filter])

  useEffect(() => { fetchContent() }, [fetchContent])

  const handleGenerate = async (request: GenerateContentRequest) => {
    const piece = await automationService.generateContent(request)
    setContent((prev) => [piece, ...prev])
    toast.success('İçerik üretildi! Onaylamak için bekliyor.')
  }

  const handleApprove = async (id: string) => {
    try {
      const updated = await automationService.approveContent({ content_id: id, action: 'approve' })
      setContent((prev) => prev.map((c) => c.id === id ? updated : c))
      toast.success('İçerik onaylandı')
    } catch { toast.error('İşlem başarısız') }
  }

  const handleReject = async (id: string) => {
    try {
      const updated = await automationService.approveContent({ content_id: id, action: 'reject' })
      setContent((prev) => prev.map((c) => c.id === id ? updated : c))
      toast.success('İçerik reddedildi')
    } catch { toast.error('İşlem başarısız') }
  }

  const handlePublish = async (id: string) => {
    try {
      const result = await automationService.publishContent(id)
      if (result.status === 'published') {
        toast.success('İçerik yayınlandı!')
        fetchContent()
      } else {
        toast.error(result.error ?? 'Yayınlama başarısız')
      }
    } catch { toast.error('Yayınlama başarısız') }
  }

  const handleDelete = async (id: string) => {
    try {
      await automationService.deleteContent(id)
      setContent((prev) => prev.filter((c) => c.id !== id))
      toast.success('İçerik silindi')
    } catch { toast.error('Silme başarısız') }
  }

  const pendingCount = content.filter((c) => c.status === 'pending_approval').length

  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-white mb-1">İçerik Otomasyonu</h2>
            <p className="text-sm text-gray-500">
              YouTube, Instagram ve Shorts için AI içerik üretin — onay verin — otomatik yayınlayın
            </p>
          </div>
          <Button onClick={() => setIsModalOpen(true)}>
            <Plus size={16} /> İçerik Üret
          </Button>
        </div>

        {pendingCount > 0 && (
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
            <p className="text-sm text-yellow-300 font-medium">
              {pendingCount} içerik onayınızı bekliyor
            </p>
          </div>
        )}

        <div className="flex items-center gap-2">
          <Filter size={14} className="text-gray-500" />
          <div className="flex gap-1.5">
            {FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => setFilter(f.value)}
                className={clsx(
                  'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                  filter === f.value
                    ? 'bg-brand-600/30 text-brand-400 border border-brand-600/40'
                    : 'bg-surface-100 text-gray-400 hover:text-gray-200 border border-surface-200'
                )}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <svg className="animate-spin h-6 w-6 text-brand-400" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        ) : content.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <Video size={48} className="text-gray-600 mb-4" />
            <p className="text-sm font-medium text-gray-400">Henüz içerik yok</p>
            <p className="text-xs text-gray-600 mt-1 mb-4">İçerik Üret butonuna tıklayarak başlayın</p>
            <Button onClick={() => setIsModalOpen(true)} variant="secondary">
              <Plus size={15} /> İlk İçeriği Oluştur
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {content.map((piece) => (
              <ContentCard
                key={piece.id}
                content={piece}
                onApprove={handleApprove}
                onReject={handleReject}
                onPublish={handlePublish}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </div>

      <GenerateContentModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onGenerate={handleGenerate}
      />
    </AppShell>
  )
}
