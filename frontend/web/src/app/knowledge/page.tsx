'use client'

import { useState, useCallback, useRef } from 'react'
import AppShell from '@/components/layout/AppShell'
import DocumentUpload from '@/components/knowledge/DocumentUpload'
import DocumentCard from '@/components/knowledge/DocumentCard'
import { useDocuments } from '@/hooks/useDocuments'
import { FileSearch, RefreshCw, Upload, X, AlertCircle, Loader2, ShieldCheck } from 'lucide-react'
import { documentService } from '@/services/document.service'
import type { Document, DocumentSourceModule } from '@/types/document'
import toast from 'react-hot-toast'

type FilterTab = 'all' | DocumentSourceModule

const TABS: { value: FilterTab; label: string }[] = [
  { value: 'all', label: 'Tümü' },
  { value: 'knowledge_center', label: 'Bilgi Merkezi' },
  { value: 'sgs_academy', label: 'SGS Akademi' },
]

export default function KnowledgePage() {
  const [activeTab, setActiveTab] = useState<FilterTab>('knowledge_center')
  const [syncing, setSyncing] = useState(false)
  const [verifying, setVerifying] = useState(false)

  // Relink modal state
  const [relinkTarget, setRelinkTarget] = useState<Document | null>(null)
  const [relinkFile, setRelinkFile] = useState<File | null>(null)
  const [relinkLoading, setRelinkLoading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const sourceModule = activeTab === 'all' ? undefined : activeTab as DocumentSourceModule
  const { documents, isLoading, isUploading, uploadDocument, deleteDocument, reindexDocument, refetch } = useDocuments(sourceModule)

  const handleSyncSgs = useCallback(async () => {
    setSyncing(true)
    try {
      const result = await documentService.syncSgs()
      if (result.synced > 0) {
        toast.success(`${result.synced} SGS belgesi senkronize edildi`)
        refetch()
      } else if (result.already_exists > 0 && result.synced === 0) {
        toast.success(`${result.already_exists} belge zaten kayıtlıydı`)
      } else {
        toast('Senkronize edilecek SGS belgesi bulunamadı', { icon: 'ℹ️' })
      }
    } catch {
      toast.error('Senkronizasyon başarısız')
    } finally {
      setSyncing(false)
    }
  }, [refetch])

  const handleVerifyStorage = useCallback(async () => {
    setVerifying(true)
    try {
      await documentService.verifyStorage()
      toast.success('Storage doğrulaması başlatıldı — liste birkaç saniye içinde güncellenir')
      setTimeout(refetch, 3000)
    } catch {
      toast.error('Storage doğrulaması başlatılamadı')
    } finally {
      setVerifying(false)
    }
  }, [refetch])

  const handleRelinkOpen = useCallback((id: string) => {
    const doc = documents.find((d) => d.id === id) ?? null
    setRelinkTarget(doc)
    setRelinkFile(null)
  }, [documents])

  const handleRelinkClose = useCallback(() => {
    setRelinkTarget(null)
    setRelinkFile(null)
  }, [])

  const handleRelinkConfirm = useCallback(async () => {
    if (!relinkTarget || !relinkFile) return
    setRelinkLoading(true)
    try {
      await documentService.relink(relinkTarget.id, relinkFile)
      toast.success('Dosya yeniden bağlandı — indeksleniyor')
      handleRelinkClose()
      setTimeout(refetch, 1500)
    } catch {
      toast.error('Dosya bağlanamadı — tekrar deneyin')
    } finally {
      setRelinkLoading(false)
    }
  }, [relinkTarget, relinkFile, refetch, handleRelinkClose])

  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in">
        {/* Başlık */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white mb-1">Bilgi Merkezi</h2>
            <p className="text-sm text-gray-500">Konu notları, ders anlatımları ve içerik üretim kaynakları</p>
          </div>
          <div className="flex gap-2 shrink-0">
            <button
              onClick={handleVerifyStorage}
              disabled={verifying}
              title="Tüm dosyaların storage'da mevcut olup olmadığını kontrol et"
              className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg bg-surface-100 hover:bg-surface-200 text-gray-400 hover:text-gray-200 transition-all disabled:opacity-50"
            >
              {verifying
                ? <Loader2 size={13} className="animate-spin" />
                : <ShieldCheck size={13} />
              }
              Dosyaları Doğrula
            </button>
            <button
              onClick={handleSyncSgs}
              disabled={syncing}
              className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg bg-surface-100 hover:bg-surface-200 text-gray-400 hover:text-gray-200 transition-all disabled:opacity-50"
            >
              <RefreshCw size={13} className={syncing ? 'animate-spin' : ''} />
              SGS Belgelerini Senkronize Et
            </button>
          </div>
        </div>

        <DocumentUpload onUpload={uploadDocument} isUploading={isUploading} />

        {/* Filtre sekmeleri */}
        <div className="flex gap-1 p-1 bg-surface-100 rounded-lg w-fit">
          {TABS.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setActiveTab(tab.value)}
              className={`text-xs px-3 py-1.5 rounded-md font-medium transition-all ${
                activeTab === tab.value
                  ? 'bg-surface-200 text-white'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Doküman listesi */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-300">
              Yüklenen Dokümanlar
              <span className="ml-2 text-xs font-normal text-gray-500">({documents.length})</span>
            </h3>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-16">
              <svg className="animate-spin h-6 w-6 text-brand-400" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </div>
          ) : documents.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <FileSearch size={40} className="text-gray-600 mb-3" />
              <p className="text-sm text-gray-500">
                {activeTab === 'sgs_academy'
                  ? 'SGS Akademi\'ye henüz belge yüklenmedi'
                  : 'Henüz doküman yüklenmedi'}
              </p>
              <p className="text-xs text-gray-600 mt-1">
                {activeTab === 'sgs_academy'
                  ? 'SGS Akademi\'ye PDF yükleyin veya "Senkronize Et" butonuna basın'
                  : 'Yukarıya PDF sürükleyerek başlayın'}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {documents.map((doc) => (
                <DocumentCard
                  key={doc.id}
                  document={doc}
                  onDelete={deleteDocument}
                  onReindex={reindexDocument}
                  onRelink={handleRelinkOpen}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Relink Modal */}
      {relinkTarget && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
          onClick={(e) => { if (e.target === e.currentTarget) handleRelinkClose() }}
        >
          <div className="bg-[#0D2040] border border-surface-200 rounded-xl w-full max-w-md p-6 shadow-2xl">
            {/* Başlık */}
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-base font-semibold text-white">Dosyayı Yeniden Bağla</h3>
                <p className="text-xs text-gray-500 mt-0.5">Kayıp dosyayı yükle — içerik verisi korunuyor</p>
              </div>
              <button
                onClick={handleRelinkClose}
                className="p-1 rounded-md hover:bg-surface-100 text-gray-500 hover:text-gray-300 transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            {/* Mevcut dosya bilgisi */}
            <div className="flex items-center gap-2 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 mb-4">
              <AlertCircle size={14} className="text-amber-400 shrink-0" />
              <span className="text-xs text-amber-300 truncate">{relinkTarget.file_name}</span>
            </div>

            {/* Dosya seçici */}
            <div
              className={`relative flex flex-col items-center justify-center gap-2 p-6 border-2 border-dashed rounded-lg cursor-pointer transition-colors ${
                relinkFile
                  ? 'border-brand-500/50 bg-brand-500/10'
                  : 'border-surface-300 hover:border-surface-200 bg-surface-100/50'
              }`}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={(e) => setRelinkFile(e.target.files?.[0] ?? null)}
              />
              {relinkFile ? (
                <>
                  <Upload size={20} className="text-brand-400" />
                  <p className="text-sm font-medium text-white text-center break-all">{relinkFile.name}</p>
                  <p className="text-xs text-gray-500">
                    {(relinkFile.size / (1024 * 1024)).toFixed(1)} MB — değiştirmek için tıkla
                  </p>
                </>
              ) : (
                <>
                  <Upload size={20} className="text-gray-500" />
                  <p className="text-sm text-gray-400">PDF dosyasını seçin</p>
                  <p className="text-xs text-gray-600">Maks 50 MB</p>
                </>
              )}
            </div>

            {/* Butonlar */}
            <div className="flex gap-2 mt-4">
              <button
                onClick={handleRelinkClose}
                disabled={relinkLoading}
                className="flex-1 py-2 text-sm rounded-lg bg-surface-100 hover:bg-surface-200 text-gray-400 hover:text-gray-200 transition-colors disabled:opacity-50"
              >
                İptal
              </button>
              <button
                onClick={handleRelinkConfirm}
                disabled={!relinkFile || relinkLoading}
                className="flex-1 py-2 text-sm rounded-lg bg-brand-600 hover:bg-brand-500 text-white font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {relinkLoading && <Loader2 size={14} className="animate-spin" />}
                {relinkLoading ? 'Yükleniyor...' : 'Yeniden Bağla'}
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  )
}
