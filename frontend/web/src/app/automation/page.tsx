'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import AppShell from '@/components/layout/AppShell'
import ContentCard from '@/components/automation/ContentCard'
import ContentEditModal from '@/components/automation/ContentEditModal'
import CleanupReportModal from '@/components/automation/CleanupReportModal'
import GenerateContentModal from '@/components/automation/GenerateContentModal'
import VideoReviewModal from '@/components/automation/VideoReviewModal'
import Button from '@/components/ui/Button'
import { automationService } from '@/services/automation.service'
import apiClient from '@/lib/api-client'
import type { ContentPiece, GenerateContentRequest } from '@/types/automation'
import { Plus, Video, Film, Filter, Trash2 } from 'lucide-react'
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
  const [editModal, setEditModal] = useState<{ id: string; title: string } | null>(null)
  const [cleanupOpen, setCleanupOpen] = useState(false)
  const [reviewContent, setReviewContent] = useState<ContentPiece | null>(null)
  const [cleanupLoading, setCleanupLoading] = useState(false)
  const [cleanupReport, setCleanupReport] = useState<null | {
    deleted_failed: number; deleted_stuck: number; deleted_corrupted: number;
    deleted_orphan: number; storage_cleaned: number; total_deleted: number
  }>(null)
  const [filter, setFilter] = useState('')
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const fetchContent = useCallback(async () => {
    try {
      const data = await automationService.listContent(filter || undefined)
      setContent(data)
      const hasGenerating = data.some((c) => c.status === 'generating')
      if (hasGenerating) {
        pollRef.current = setTimeout(fetchContent, 12000)
      }
    } catch {
      toast.error('İçerikler yüklenemedi')
    } finally {
      setIsLoading(false)
    }
  }, [filter])

  useEffect(() => {
    fetchContent()
    return () => { if (pollRef.current) clearTimeout(pollRef.current) }
  }, [fetchContent])

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

  const handleEdit = (id: string, title: string) => {
    setEditModal({ id, title })
  }

  const handleRetry = async (id: string) => {
    try {
      await apiClient.post(`/content/${id}/retry`)
      setContent(prev => prev.map(c => c.id === id ? { ...c, status: 'generating' } : c))
      toast.success('Yeniden üretim başladı')
      if (pollRef.current) clearTimeout(pollRef.current)
      pollRef.current = setTimeout(fetchContent, 8000)
    } catch { toast.error('Yeniden üretim başlatılamadı') }
  }

  const handleArchive = async (id: string) => {
    try {
      await apiClient.patch(`/content/${id}/archive`)
      setContent(prev => prev.map(c => c.id === id ? { ...c, status: 'archived' } : c))
      toast.success('İçerik arşivlendi')
    } catch { toast.error('Arşivleme başarısız') }
  }

  const handleCleanup = async () => {
    setCleanupOpen(true)
    setCleanupLoading(true)
    setCleanupReport(null)
    try {
      const { data } = await apiClient.post('/content/cleanup')
      setCleanupReport(data)
      if (data.total_deleted > 0) fetchContent()
    } catch {
      setCleanupReport(null)
    } finally {
      setCleanupLoading(false)
    }
  }

  const handleEditRegenerated = (id: string) => {
    setContent(prev => prev.map(c => c.id === id ? { ...c, status: 'generating' } : c))
    if (pollRef.current) clearTimeout(pollRef.current)
    pollRef.current = setTimeout(fetchContent, 8000)
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
          <div className="flex gap-2">
            <button
              onClick={handleCleanup}
              title="Hatalı, yetim ve takılı içerikleri temizle"
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-gray-400 hover:text-orange-400 bg-surface-100 border border-surface-200 rounded-xl transition-colors"
            >
              <Trash2 size={13} /> Sistem Temizliği
            </button>
            <Button onClick={() => setIsModalOpen(true)}>
              <Plus size={16} /> İçerik Üret
            </Button>
          </div>
        </div>

        {pendingCount > 0 && (
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
            <p className="text-sm text-yellow-300 font-medium">
              {pendingCount} içerik onayınızı bekliyor
            </p>
          </div>
        )}

        {/* Video Production yönlendirmesi */}
        <div className="bg-surface-50 border border-surface-200 rounded-xl px-4 py-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <Film size={16} className="text-blue-400 shrink-0" />
            <p className="text-xs text-gray-400">
              Konu anlatım ve soru çözüm videoları <strong className="text-gray-300">Video Prodüksiyon</strong>&apos;da üretilir. Onaylanan videolar buraya otomatik aktarılır.
            </p>
          </div>
          <a
            href="/video"
            className="shrink-0 text-xs font-semibold text-blue-400 hover:text-blue-200 underline underline-offset-2 transition-colors whitespace-nowrap"
          >
            Video Prodüksiyon →
          </a>
        </div>

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
                onEdit={handleEdit}
                onRetry={handleRetry}
                onArchive={handleArchive}
                onReview={setReviewContent}
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

      {editModal && (
        <ContentEditModal
          contentId={editModal.id}
          contentTitle={editModal.title}
          isOpen={!!editModal}
          onClose={() => setEditModal(null)}
          onRegenerated={handleEditRegenerated}
        />
      )}

      <CleanupReportModal
        isOpen={cleanupOpen}
        onClose={() => setCleanupOpen(false)}
        report={cleanupReport}
        loading={cleanupLoading}
      />

      <VideoReviewModal
        content={reviewContent}
        onClose={() => setReviewContent(null)}
        onApprove={(id) => { handleApprove(id); setReviewContent(null) }}
        onReject={(id) => { handleReject(id); setReviewContent(null) }}
        onPublish={(id) => { handlePublish(id); setReviewContent(null) }}
      />
    </AppShell>
  )
}
