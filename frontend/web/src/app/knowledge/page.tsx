'use client'

import AppShell from '@/components/layout/AppShell'
import DocumentUpload from '@/components/knowledge/DocumentUpload'
import DocumentCard from '@/components/knowledge/DocumentCard'
import { useDocuments } from '@/hooks/useDocuments'
import { FileSearch } from 'lucide-react'

export default function KnowledgePage() {
  const { documents, isLoading, isUploading, uploadDocument, deleteDocument, reindexDocument } = useDocuments()

  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in">
        <div>
          <h2 className="text-xl font-bold text-white mb-1">Bilgi Tabanı</h2>
          <p className="text-sm text-gray-500">PDF ve dokümanlarınızı yükleyin, AI&apos;ın öğrenmesini sağlayın</p>
        </div>

        <DocumentUpload onUpload={uploadDocument} isUploading={isUploading} />

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
              <p className="text-sm text-gray-500">Henüz doküman yüklenmedi</p>
              <p className="text-xs text-gray-600 mt-1">Yukarıya PDF sürükleyerek başlayın</p>
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
