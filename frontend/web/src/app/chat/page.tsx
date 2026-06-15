'use client'

import { useRef, useEffect } from 'react'
import AppShell from '@/components/layout/AppShell'
import MessageBubble from '@/components/chat/MessageBubble'
import ChatInput from '@/components/chat/ChatInput'
import { useChat } from '@/hooks/useChat'
import { MessageSquare, Trash2 } from 'lucide-react'

export default function ChatPage() {
  const { messages, isLoading, sendMessage, clearChat } = useChat()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <AppShell>
      <div className="flex flex-col h-full animate-fade-in" style={{ height: 'calc(100vh - 64px - 48px)' }}>
        <div className="flex items-center justify-between mb-4 flex-shrink-0">
          <div>
            <h2 className="text-xl font-bold text-white">Chat</h2>
            <p className="text-sm text-gray-500">Bilgi tabanınıza yazılı soru sorun</p>
          </div>
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="flex items-center gap-2 text-xs text-gray-500 hover:text-gray-300 px-3 py-1.5 rounded-lg hover:bg-surface-100 transition-colors"
            >
              <Trash2 size={13} /> Temizle
            </button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto space-y-4 pr-1 pb-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="p-5 bg-surface-100 rounded-2xl mb-4">
                <MessageSquare size={40} className="text-gray-500" />
              </div>
              <p className="text-sm font-medium text-gray-400 mb-1">Soru sormaya başlayın</p>
              <p className="text-xs text-gray-600 max-w-sm">
                Yüklediğiniz dokümanlar hakkında her şeyi sorabilirsiniz. AI kaynak göstererek cevap verir.
              </p>
              <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-md">
                {[
                  'SGS sınavı başvuru şartları nelerdir?',
                  'İş başvurusu için hangi belgeler gerekli?',
                  'Müşteri ile nasıl iletişim kurulmalı?',
                  'Bu aydaki eğitim programları neler?',
                ].map((q) => (
                  <button
                    key={q}
                    onClick={() => sendMessage(q)}
                    className="text-left text-xs text-gray-400 bg-surface-50 border border-surface-200 hover:border-surface-300 rounded-lg px-3 py-2.5 hover:text-gray-300 transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
          )}

          {isLoading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-surface-200 flex items-center justify-center flex-shrink-0 mt-1">
                <div className="w-3 h-3 rounded-full bg-gray-500 animate-pulse" />
              </div>
              <div className="bg-surface-100 rounded-2xl rounded-tl-sm px-4 py-3">
                <div className="flex gap-1.5 items-center h-5">
                  <div className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="flex-shrink-0 pt-2">
          <ChatInput onSend={sendMessage} isLoading={isLoading} />
        </div>
      </div>
    </AppShell>
  )
}
