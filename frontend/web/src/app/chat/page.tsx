'use client'

import { useRef, useEffect } from 'react'
import AppShell from '@/components/layout/AppShell'
import MessageBubble from '@/components/chat/MessageBubble'
import ChatInput from '@/components/chat/ChatInput'
import { useChat } from '@/hooks/useChat'
import { MessageSquare, Plus, Trash2, Clock } from 'lucide-react'
import { clsx } from 'clsx'

const QUICK_QUESTIONS = [
  'KDV beyannamesi ne zaman verilir?',
  'SGK bildirgesi nasıl hazırlanır?',
  'Muhasebe dönem sonu işlemleri nelerdir?',
  'SGS sertifika başvuru şartları nedir?',
]

export default function ChatPage() {
  const {
    messages,
    conversations,
    activeConversationId,
    isLoading,
    isHistoryLoading,
    sendMessage,
    loadConversation,
    startNewChat,
    deleteConversation,
  } = useChat()

  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <AppShell>
      <div className="flex h-full gap-4 animate-fade-in" style={{ height: 'calc(100vh - 64px - 48px)' }}>

        {/* Conversation list sidebar */}
        <div className="w-56 flex-shrink-0 flex flex-col gap-2">
          <button
            onClick={startNewChat}
            className="flex items-center gap-2 px-3 py-2 bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium rounded-xl transition-colors w-full"
          >
            <Plus size={15} />
            Yeni Sohbet
          </button>

          <div className="flex-1 overflow-y-auto space-y-1">
            {conversations.length === 0 ? (
              <p className="text-xs text-gray-600 text-center mt-4">Henüz sohbet yok</p>
            ) : (
              conversations.map((conv) => (
                <div
                  key={conv.id}
                  className={clsx(
                    'group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors text-xs',
                    activeConversationId === conv.id
                      ? 'bg-brand-600/20 text-brand-400 border border-brand-600/30'
                      : 'text-gray-400 hover:bg-surface-100 hover:text-gray-200'
                  )}
                  onClick={() => loadConversation(conv.id)}
                >
                  <MessageSquare size={12} className="flex-shrink-0" />
                  <span className="flex-1 truncate">{conv.title || 'Sohbet'}</span>
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteConversation(conv.id) }}
                    className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:text-red-400 transition-all"
                  >
                    <Trash2 size={11} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Chat area */}
        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex items-center justify-between mb-3 flex-shrink-0">
            <div>
              <h2 className="text-lg font-bold text-white">Chat</h2>
              <p className="text-xs text-gray-500">Bilgi bankasına bağlı AI asistan</p>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto space-y-4 pr-1 pb-4">
            {isHistoryLoading ? (
              <div className="flex items-center justify-center h-full">
                <svg className="animate-spin h-5 w-5 text-brand-400" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              </div>
            ) : messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <div className="p-5 bg-surface-100 rounded-2xl mb-4">
                  <MessageSquare size={40} className="text-gray-500" />
                </div>
                <p className="text-sm font-medium text-gray-400 mb-1">Soru sormaya başlayın</p>
                <p className="text-xs text-gray-600 max-w-sm mb-6">
                  Yüklediğiniz dokümanlar hakkında soru sorun. AI kaynak göstererek cevap üretir.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg w-full">
                  {QUICK_QUESTIONS.map((q) => (
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
              messages.map((msg, i) => <MessageBubble key={msg.id || i} message={msg} />)
            )}

            {isLoading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-surface-200 flex items-center justify-center flex-shrink-0 mt-1">
                  <div className="w-3 h-3 rounded-full bg-gray-500 animate-pulse" />
                </div>
                <div className="bg-surface-100 rounded-2xl rounded-tl-sm px-4 py-3">
                  <div className="flex gap-1.5 items-center h-5">
                    {[0, 150, 300].map((delay) => (
                      <div
                        key={delay}
                        className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce"
                        style={{ animationDelay: `${delay}ms` }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="flex-shrink-0 pt-2">
            <ChatInput onSend={sendMessage} isLoading={isLoading} />
            {activeConversationId && (
              <div className="flex items-center gap-1 mt-1.5 px-1">
                <Clock size={10} className="text-gray-600" />
                <span className="text-xs text-gray-600">Bu sohbet kaydediliyor</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  )
}
