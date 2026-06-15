'use client'

import { useState } from 'react'
import Sidebar from './Sidebar'
import Header from './Header'
import AssistantWidget from '@/components/assistant/AssistantWidget'

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [assistantOpen, setAssistantOpen] = useState(false)

  return (
    <div className="flex h-screen bg-surface overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header onOpenAssistant={() => setAssistantOpen(true)} />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
      <AssistantWidget
        isOpen={assistantOpen}
        onOpen={() => setAssistantOpen(true)}
        onClose={() => setAssistantOpen(false)}
      />
    </div>
  )
}
