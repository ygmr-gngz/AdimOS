'use client'

import { useState } from 'react'
import Sidebar from './Sidebar'
import Header from './Header'
import AssistantWidget from '@/components/assistant/AssistantWidget'
import ErrorBoundary from '@/components/ui/ErrorBoundary'

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [assistantOpen, setAssistantOpen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="flex h-screen bg-surface overflow-hidden">
      <ErrorBoundary label="Kenar çubuğu yüklenemedi">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      </ErrorBoundary>
      <div className="flex-1 flex flex-col min-w-0">
        <ErrorBoundary label="Başlık çubuğu yüklenemedi">
          <Header
            onOpenAssistant={() => setAssistantOpen(true)}
            onOpenSidebar={() => setSidebarOpen(true)}
          />
        </ErrorBoundary>
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </main>
      </div>
      <ErrorBoundary label="Asistan yüklenemedi">
        <AssistantWidget
          isOpen={assistantOpen}
          onOpen={() => setAssistantOpen(true)}
          onClose={() => setAssistantOpen(false)}
        />
      </ErrorBoundary>
    </div>
  )
}
