'use client'

import { useState, useRef, useEffect } from 'react'
import { X, Send, Sparkles, CheckCircle, RefreshCw } from 'lucide-react'
import apiClient from '@/lib/api-client'
import toast from 'react-hot-toast'

interface Message {
  role: 'user' | 'assistant'
  text: string
  changes?: string[]
}

const QUICK_EDITS = [
  'Bu videoyu daha uzun yap',
  'Daha fazla örnek ekle',
  'Daha profesyonel bir ton kullan',
  'Daha kısa ve öz olsun',
  'Daha öğretici yap',
  'Daha hareketli ve dinamik olsun',
  'Çıkmış soru ekle',
  'Özeti güçlendir',
]

interface Props {
  contentId: string
  contentTitle: string
  isOpen: boolean
  onClose: () => void
  onRegenerated: (id: string) => void
}

export default function ContentEditModal({ contentId, contentTitle, isOpen, onClose, onRegenerated }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [regenerated, setRegenerated] = useState(false)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isOpen) {
      setMessages([])
      setInput('')
      setRegenerated(false)
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [isOpen, contentId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (text?: string) => {
    const msg = (text ?? input).trim()
    if (!msg || sending) return
    setInput('')
    setSending(true)

    setMessages(prev => [...prev, { role: 'user', text: msg }])

    try {
      const { data } = await apiClient.post(`/content/${contentId}/edit`, { message: msg })
      const changes: string[] = data.changes_summary ?? []
      const explanation: string = data.explanation ?? ''
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          text: explanation || 'Düzenleme planı oluşturuldu. İçerik yeniden üretiliyor...',
          changes,
        },
      ])
      setRegenerated(true)
      onRegenerated(contentId)
      toast.success('İçerik yeniden üretiliyor')
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Düzenleme başlatılamadı. Tekrar deneyin.' }])
      toast.error('Düzenleme başarısız')
    } finally {
      setSending(false)
    }
  }

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Panel */}
      <div className="relative w-full sm:max-w-lg bg-surface-50 border border-surface-200 rounded-t-2xl sm:rounded-2xl shadow-2xl flex flex-col max-h-[85vh] sm:max-h-[600px]">

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-surface-200">
          <div className="flex items-center gap-2 min-w-0">
            <Sparkles size={16} className="text-brand-400 shrink-0" />
            <div className="min-w-0">
              <p className="text-sm font-semibold text-white">İçerik Düzenle</p>
              <p className="text-xs text-gray-500 truncate">{contentTitle}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-gray-500 hover:text-gray-300 transition-colors">
            <X size={16} />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {messages.length === 0 && (
            <div className="space-y-3">
              <p className="text-xs text-gray-500">
                İçeriği nasıl değiştirmek istediğini yaz. Sistem analiz eder ve yeniden üretir.
              </p>
              <div className="flex flex-wrap gap-2">
                {QUICK_EDITS.map(q => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    disabled={sending}
                    className="text-xs px-3 py-1.5 bg-surface-100 hover:bg-surface-200 border border-surface-300 text-gray-400 hover:text-gray-200 rounded-lg transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[85%] rounded-xl px-4 py-2.5 text-sm ${
                  m.role === 'user'
                    ? 'bg-brand-600/30 border border-brand-600/20 text-brand-100'
                    : 'bg-surface-100 border border-surface-200 text-gray-300'
                }`}
              >
                <p className="leading-relaxed">{m.text}</p>
                {m.changes && m.changes.length > 0 && (
                  <ul className="mt-2 space-y-1 border-t border-surface-300 pt-2">
                    {m.changes.map((c, j) => (
                      <li key={j} className="flex items-start gap-1.5 text-xs text-gray-400">
                        <CheckCircle size={11} className="text-green-400 mt-0.5 shrink-0" />
                        {c}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          ))}

          {sending && (
            <div className="flex justify-start">
              <div className="bg-surface-100 border border-surface-200 rounded-xl px-4 py-2.5">
                <div className="flex gap-1">
                  {[0, 150, 300].map(d => (
                    <div key={d} className="w-1.5 h-1.5 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: `${d}ms` }} />
                  ))}
                </div>
              </div>
            </div>
          )}

          {regenerated && !sending && (
            <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-xl flex items-center gap-2">
              <RefreshCw size={13} className="text-green-400 animate-spin" />
              <p className="text-xs text-green-300">
                Yeniden üretim başladı. İçerik sayfasında takip edebilirsiniz.
              </p>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="px-5 py-4 border-t border-surface-200">
          <div className="flex items-end gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Düzenleme isteğini yaz... (Enter ile gönder)"
              rows={2}
              disabled={sending || regenerated}
              className="flex-1 resize-none bg-surface-100 border border-surface-300 rounded-xl px-3 py-2.5 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-brand-500 transition-colors disabled:opacity-50"
            />
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || sending || regenerated}
              className="p-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl transition-colors shrink-0"
            >
              <Send size={16} />
            </button>
          </div>
          <p className="text-xs text-gray-700 mt-1.5">
            Enter ile gönder · Shift+Enter yeni satır
          </p>
        </div>
      </div>
    </div>
  )
}
