'use client'

import { useEffect, useState } from 'react'
import AppShell from '@/components/layout/AppShell'
import { instagramDmsService, type InstagramConversation, type InstagramMessage } from '@/services/instagram-dms.service'
import { Instagram, MessageCircle, Send, FlaskConical, ChevronRight, User, Bot } from 'lucide-react'
import { clsx } from 'clsx'
import toast from 'react-hot-toast'

const INTEREST_LABELS: Record<string, string> = {
  randevu: 'Randevu',
  bilgi: 'Bilgi',
  cikmis_sorular: 'Çıkmış Sorular',
}

const STEP_LABELS: Record<string, string> = {
  init: 'Yeni',
  menu: 'Menüde',
  flow_randevu: 'Randevu',
  flow_bilgi: 'Bilgi',
  flow_cikmis_sorular: 'Soru',
  flow_link: 'Link',
}

/* ── Test Paneli ─────────────────────────────────────────────── */
function TestPanel() {
  const [text, setText] = useState('')
  const [result, setResult] = useState<{ reply: string; matched_flow: string | null; would_create_crm_lead: boolean } | null>(null)
  const [loading, setLoading] = useState(false)

  const handleTest = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim()) return
    setLoading(true)
    try {
      const res = await instagramDmsService.testDmFlow('test_user', text.trim())
      setResult(res)
    } catch {
      toast.error('Test başarısız')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-surface-50 rounded-xl border border-surface-200 p-5">
      <div className="flex items-center gap-2 mb-4">
        <FlaskConical size={15} className="text-brand-400" />
        <h3 className="text-sm font-semibold text-gray-200">DM Akışı Test Et</h3>
        <span className="text-xs text-gray-600">— Gerçek Instagram&apos;a mesaj göndermez</span>
      </div>
      <form onSubmit={handleTest} className="flex gap-2 mb-4">
        <input
          className="flex-1 bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500 placeholder-gray-600"
          placeholder="örn: randevu, 1, bilgi, youtube..."
          value={text}
          onChange={e => setText(e.target.value)}
        />
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
        >
          Test Et
        </button>
      </form>
      {result && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span>Eşleşen flow: <strong className="text-brand-300">{result.matched_flow ?? 'Yok (fallback)'}</strong></span>
            {result.would_create_crm_lead && (
              <span className="bg-green-500/15 text-green-400 px-2 py-0.5 rounded-full">CRM lead oluşturulur</span>
            )}
          </div>
          <div className="bg-surface-100 rounded-xl p-3 border border-surface-200">
            <p className="text-xs font-medium text-gray-500 mb-1.5">Bot cevabı:</p>
            <p className="text-sm text-gray-300 whitespace-pre-wrap">{result.reply}</p>
          </div>
        </div>
      )}
    </div>
  )
}

/* ── Mesaj Balonu ────────────────────────────────────────────── */
function MessageBubble({ msg, ownId }: { msg: InstagramMessage; ownId: string }) {
  const isOutbound = msg.direction === 'outbound' || msg.sender_id === ownId
  return (
    <div className={clsx('flex gap-2 mb-3', isOutbound ? 'flex-row-reverse' : 'flex-row')}>
      <div className={clsx('w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs', isOutbound ? 'bg-brand-600/30' : 'bg-surface-200')}>
        {isOutbound ? <Bot size={13} className="text-brand-400" /> : <User size={13} className="text-gray-400" />}
      </div>
      <div className={clsx('max-w-[75%] rounded-2xl px-4 py-2.5 text-sm', isOutbound ? 'bg-brand-600/20 text-gray-200 rounded-tr-sm' : 'bg-surface-100 text-gray-300 rounded-tl-sm')}>
        <p className="whitespace-pre-wrap leading-relaxed">{msg.message_text}</p>
        <p className="text-[10px] text-gray-600 mt-1">{new Date(msg.created_at).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}</p>
      </div>
    </div>
  )
}

/* ── Ana Sayfa ───────────────────────────────────────────────── */
export default function InstagramDmsPage() {
  const [conversations, setConversations] = useState<InstagramConversation[]>([])
  const [selected, setSelected] = useState<InstagramConversation | null>(null)
  const [messages, setMessages] = useState<InstagramMessage[]>([])
  const [replyText, setReplyText] = useState('')
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'conversations' | 'test'>('conversations')

  useEffect(() => {
    instagramDmsService.listConversations()
      .then(setConversations)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const handleSelect = async (conv: InstagramConversation) => {
    setSelected(conv)
    try {
      const msgs = await instagramDmsService.getMessages(conv.instagram_user_id)
      setMessages(msgs)
    } catch {
      toast.error('Mesajlar yüklenemedi')
    }
  }

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!replyText.trim() || !selected) return
    setSending(true)
    try {
      await instagramDmsService.sendMessage(selected.instagram_user_id, replyText.trim())
      toast.success('Mesaj gönderildi')
      setReplyText('')
      const msgs = await instagramDmsService.getMessages(selected.instagram_user_id)
      setMessages(msgs)
    } catch {
      toast.error('Mesaj gönderilemedi')
    } finally {
      setSending(false)
    }
  }

  return (
    <AppShell>
      <div className="space-y-5 animate-fade-in">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Instagram size={20} className="text-pink-400" />
            <h2 className="text-xl font-bold text-white">Instagram DM</h2>
          </div>
          <div className="flex gap-1 bg-surface-100 p-1 rounded-xl">
            {(['conversations', 'test'] as const).map(t => (
              <button key={t} onClick={() => setTab(t)}
                className={clsx('px-4 py-1.5 rounded-lg text-sm font-medium transition-colors', tab === t ? 'bg-surface-50 text-white shadow-sm' : 'text-gray-500 hover:text-gray-300')}>
                {t === 'conversations' ? `Konuşmalar (${conversations.length})` : 'Test Akışı'}
              </button>
            ))}
          </div>
        </div>

        {tab === 'test' && <TestPanel />}

        {tab === 'conversations' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4" style={{ minHeight: 500 }}>
            {/* Sol: Konuşma listesi */}
            <div className="bg-surface-50 rounded-xl border border-surface-200 overflow-hidden">
              <div className="px-4 py-3 border-b border-surface-200">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Konuşmalar</p>
              </div>
              {loading ? (
                <div className="p-6 text-center text-gray-600 text-sm">Yükleniyor...</div>
              ) : conversations.length === 0 ? (
                <div className="p-6 text-center">
                  <MessageCircle size={24} className="text-gray-700 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">Henüz DM yok</p>
                  <p className="text-xs text-gray-700 mt-1">Webhook bağlandıktan sonra mesajlar burada görünecek</p>
                </div>
              ) : (
                <div className="divide-y divide-surface-200 overflow-y-auto" style={{ maxHeight: 500 }}>
                  {conversations.map(conv => (
                    <button key={conv.id} onClick={() => handleSelect(conv)}
                      className={clsx('w-full text-left px-4 py-3 hover:bg-surface-100 transition-colors flex items-center justify-between gap-2',
                        selected?.id === conv.id ? 'bg-surface-100 border-l-2 border-brand-500' : '')}>
                      <div className="min-w-0">
                        <p className="text-xs font-mono text-gray-400 truncate">{conv.instagram_user_id}</p>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          {conv.interest && (
                            <span className="text-[10px] bg-brand-600/20 text-brand-400 px-1.5 py-0.5 rounded-full">
                              {INTEREST_LABELS[conv.interest] ?? conv.interest}
                            </span>
                          )}
                          <span className="text-[10px] text-gray-600">
                            {STEP_LABELS[conv.current_step] ?? conv.current_step}
                          </span>
                        </div>
                      </div>
                      <ChevronRight size={14} className="text-gray-600 shrink-0" />
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Sağ: Mesajlar */}
            <div className="md:col-span-2 bg-surface-50 rounded-xl border border-surface-200 flex flex-col overflow-hidden">
              {selected ? (
                <>
                  <div className="px-4 py-3 border-b border-surface-200 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-gray-200">{selected.instagram_user_id}</p>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        {selected.interest && <span>{INTEREST_LABELS[selected.interest]}</span>}
                        {selected.crm_lead_id && <span className="text-green-400">• CRM kaydı var</span>}
                      </div>
                    </div>
                  </div>
                  <div className="flex-1 overflow-y-auto p-4">
                    {messages.length === 0 ? (
                      <p className="text-center text-xs text-gray-600 mt-8">Mesaj yok</p>
                    ) : (
                      messages.map(msg => (
                        <MessageBubble key={msg.id} msg={msg} ownId={selected.instagram_user_id} />
                      ))
                    )}
                  </div>
                  <form onSubmit={handleSend} className="px-4 py-3 border-t border-surface-200 flex gap-2">
                    <input
                      className="flex-1 bg-surface-100 border border-surface-200 rounded-xl px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500 placeholder-gray-600"
                      placeholder="Manuel mesaj yaz..."
                      value={replyText}
                      onChange={e => setReplyText(e.target.value)}
                    />
                    <button type="submit" disabled={sending || !replyText.trim()}
                      className="p-2.5 bg-brand-600 hover:bg-brand-500 text-white rounded-xl transition-colors disabled:opacity-50">
                      <Send size={16} />
                    </button>
                  </form>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center text-gray-600 text-sm">
                  ← Bir konuşma seçin
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  )
}
