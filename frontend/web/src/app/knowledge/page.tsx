'use client'

import { useState, useCallback } from 'react'
import AppShell from '@/components/layout/AppShell'
import DocumentUpload from '@/components/knowledge/DocumentUpload'
import DocumentCard from '@/components/knowledge/DocumentCard'
import { useDocuments } from '@/hooks/useDocuments'
import { FileSearch, RefreshCw } from 'lucide-react'
import { documentService } from '@/services/document.service'
import type { DocumentSourceModule } from '@/types/document'
import toast from 'react-hot-toast'

type FilterTab = 'all' | DocumentSourceModule

const TABS: { value: FilterTab; label: string }[] = [
  { value: 'all', label: 'Tümü' },
  { value: 'knowledge_center', label: 'Bilgi Merkezi' },
  { value: 'sgs_academy', label: 'SGS Akademi' },
]

export default function KnowledgePage() {
  const [activeTab, setActiveTab] = useState<FilterTab>('all')
  const [syncing, setSyncing] = useState(false)

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

  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white mb-1">Bilgi Tabanı</h2>
            <p className="text-sm text-gray-500">PDF ve dokümanlarınızı yükleyin, AI&apos;ın öğrenmesini sağlayın</p>
          </div>
          <button
            onClick={handleSyncSgs}
            disabled={syncing}
            className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg bg-surface-100 hover:bg-surface-200 text-gray-400 hover:text-gray-200 transition-all disabled:opacity-50 shrink-0"
          >
            <RefreshCw size={13} className={syncing ? 'animate-spin' : ''} />
            SGS Belgelerini Senkronize Et
          </button>
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
                <DocumentCard key={doc.id} document={doc} onDelete={deleteDocument} onReindex={reindexDocument} />
              ))}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  )
}
