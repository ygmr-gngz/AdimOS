'use client'

import { useCallback, useEffect, useState } from 'react'
import AppShell from '@/components/layout/AppShell'
import { widgetService } from '@/services/widget.service'
import type { WidgetConversation, WidgetStats } from '@/types/widget'
import {
  MessageSquare,
  Users,
  FileText,
  TrendingUp,
  ChevronRight,
  X,
  Bot,
  Mic,
  Search,
  RefreshCw,
} from 'lucide-react'
import { clsx } from 'clsx'

function StatCard({
  label,
  value,
  icon: Icon,
  colorClass,
}: {
  label: string
  value: number
  icon: React.ElementType
  colorClass: string
}) {
  return (
    <div className="bg-surface-50 border border-surface-200 rounded-xl p-4 flex items-center gap-4">
      <div className={clsx('p-3 rounded-lg flex-shrink-0', colorClass)}>
        <Icon size={18} />
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{value.toLocaleString('tr-TR')}</p>
        <p className="text-xs text-gray-500 mt-0.5">{label}</p>
      </div>
    </div>
  )
}

function ConversationModal({
  conv,
  onClose,
}: {
  conv: WidgetConversation
  onClose: () => void
}) {
  const [full, setFull] = useState<WidgetConversation | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    widgetService
      .getConversation(conv.id)
      .then(setFull)
      .catch(() => setFull(conv))
      .finally(() => setLoading(false))
  }, [conv])

  const messages = full?.messages ?? []

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg bg-surface-50 border border-surface-200 rounded-2xl shadow-2xl flex flex-col max-h-[80vh]">
        {/* Modal header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-surface-200 flex-shrink-0">
          <div>
            <p className="text-sm font-semibold text-white">
              {conv.visitor_name ?? `Ziyaretçi ${conv.visitor_id.slice(-6)}`}
            </p>
            <p className="text-xs text-gray-500 mt-0.5">
              {new Date(conv.started_at).toLocaleString('tr-TR')} &middot;{' '}
              {conv.message_count} mesaj
              {conv.file_count > 0 && ` · ${conv.file_count} dosya`}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-surface-100 text-gray-500 hover:text-gray-200 transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="w-6 h-6 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : messages.length === 0 ? (
            <p className="text-center text-sm text-gray-600 py-12">Mesaj bulunamadı</p>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={clsx('flex gap-2', msg.role === 'visitor' ? 'flex-row-reverse' : '')}
              >
                {msg.role === 'assistant' && (
                  <div className="w-6 h-6 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Bot size={11} className="text-white" />
                  </div>
                )}
                <div
                  className={clsx(
                    'max-w-[80%] px-3 py-2 rounded-2xl text-sm leading-relaxed',
                    msg.role === 'visitor'
                      ? 'bg-brand-600 text-white rounded-tr-sm'
                      : 'bg-surface-100 text-gray-200 rounded-tl-sm'
                  )}
                >
                  {msg.input_type === 'voice' && msg.role === 'visitor' && (
                    <div className="flex items-center gap-1 mb-1 opacity-60">
                      <Mic size={9} />
                      <span className="text-[10px]">sesli</span>
                    </div>
                  )}
                  {msg.files?.map((f, i) => (
                    <div key={i} className="flex items-center gap-1.5 text-xs opacity-75 mb-1">
                      <FileText size={10} /> {f.name}
                    </div>
                  ))}
                  {msg.content}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default function WebsitePage() {
  const [stats, setStats] = useState<WidgetStats | null>(null)
  const [conversations, setConversations] = useState<WidgetConversation[]>([])
  const [filtered, setFiltered] = useState<WidgetConversation[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selected, setSelected] = useState<WidgetConversation | null>(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'closed'>('all')

  const fetchData = useCallback(async () => {
    setIsLoading(true)
    try {
      const [s, c] = await Promise.all([
        widgetService.getStats(),
        widgetService.getConversations(),
      ])
      setStats(s)
      setConversations(c)
      setFiltered(c)
    } catch {
      // backend bağlı değil
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  // Filtrele
  useEffect(() => {
    let list = conversations
    if (statusFilter !== 'all') list = list.filter(c => c.status === statusFilter)
    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter(c =>
        (c.visitor_name ?? '').toLowerCase().includes(q) ||
        c.visitor_id.toLowerCase().includes(q)
      )
    }
    setFiltered(list)
  }, [conversations, search, statusFilter])

  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in">
        {/* Başlık */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">Web Sitesi Konuşmaları</h2>
            <p className="text-sm text-gray-500 mt-1">
              Chatbot üzerinden gelen ziyaretçi sorularını buradan takip edin
            </p>
          </div>
          <button
            onClick={fetchData}
            disabled={isLoading}
            className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-200 border border-surface-200 hover:border-surface-300 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-40"
          >
            <RefreshCw size={13} className={isLoading ? 'animate-spin' : ''} />
            Yenile
          </button>
        </div>

        {/* İstatistik kartları */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Toplam Konuşma"
            value={stats?.total_conversations ?? 0}
            icon={MessageSquare}
            colorClass="bg-brand-600/10 text-brand-400"
          />
          <StatCard
            label="Bugün"
            value={stats?.today_conversations ?? 0}
            icon={TrendingUp}
            colorClass="bg-green-500/10 text-green-400"
          />
          <StatCard
            label="Aktif Konuşma"
            value={stats?.active_conversations ?? 0}
            icon={Users}
            colorClass="bg-orange-500/10 text-orange-400"
          />
          <StatCard
            label="Dosya Yükleme"
            value={stats?.total_file_uploads ?? 0}
            icon={FileText}
            colorClass="bg-purple-500/10 text-purple-400"
          />
        </div>

        {/* Konuşma listesi */}
        <div className="bg-surface-50 border border-surface-200 rounded-xl overflow-hidden">
          {/* Tablo başlığı + filtreler */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 px-4 py-3 border-b border-surface-200">
            <h3 className="text-sm font-semibold text-white flex-1">Ziyaretçi Konuşmaları</h3>

            {/* Durum filtresi */}
            <div className="flex items-center gap-1 bg-surface-100 rounded-lg p-0.5 text-xs">
              {(['all', 'active', 'closed'] as const).map(s => (
                <button
                  key={s}
                  onClick={() => setStatusFilter(s)}
                  className={clsx(
                    'px-3 py-1 rounded-md transition-colors font-medium',
                    statusFilter === s
                      ? 'bg-brand-600 text-white'
                      : 'text-gray-500 hover:text-gray-300'
                  )}
                >
                  {s === 'all' ? 'Tümü' : s === 'active' ? 'Aktif' : 'Kapalı'}
                </button>
              ))}
            </div>

            {/* Arama */}
            <div className="flex items-center gap-2 bg-surface-100 border border-surface-200 rounded-lg px-3 py-1.5">
              <Search size={13} className="text-gray-500 flex-shrink-0" />
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Ziyaretçi ara..."
                className="bg-transparent text-xs text-gray-200 placeholder-gray-600 outline-none w-32"
              />
            </div>
          </div>

          {/* Liste */}
          {isLoading ? (
            <div className="flex justify-center py-16">
              <div className="w-6 h-6 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <MessageSquare size={32} className="text-gray-600 mb-3" />
              <p className="text-sm text-gray-500">
                {conversations.length === 0
                  ? 'Henüz konuşma yok'
                  : 'Arama kriterine uygun konuşma bulunamadı'}
              </p>
              {conversations.length === 0 && (
                <p className="text-xs text-gray-600 mt-1">
                  Web sitenize chatbot eklendikten sonra ziyaretçi soruları burada görünür
                </p>
              )}
            </div>
          ) : (
            <div className="divide-y divide-surface-200">
              {filtered.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => setSelected(conv)}
                  className="w-full flex items-center justify-between px-4 py-3.5 hover:bg-surface-100 transition-colors text-left group"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    {/* Avatar */}
                    <div className="w-8 h-8 rounded-full bg-brand-600/15 border border-brand-600/25 flex items-center justify-center flex-shrink-0">
                      <span className="text-xs font-bold text-brand-400">
                        {(conv.visitor_name ?? conv.visitor_id).slice(0, 1).toUpperCase()}
                      </span>
                    </div>

                    {/* Bilgiler */}
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-gray-200">
                        {conv.visitor_name ?? `Ziyaretçi #${conv.visitor_id.slice(-6)}`}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {new Date(conv.last_message_at).toLocaleString('tr-TR', {
                          day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
                        })}
                        {' · '}{conv.message_count} mesaj
                        {conv.file_count > 0 && (
                          <span className="ml-1.5 text-purple-400">
                            <FileText size={10} className="inline -mt-0.5 mr-0.5" />
                            {conv.file_count}
                          </span>
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0 ml-3">
                    <span
                      className={clsx(
                        'text-xs px-2 py-0.5 rounded-full border',
                        conv.status === 'active'
                          ? 'bg-green-500/10 text-green-400 border-green-500/20'
                          : 'bg-surface-100 text-gray-500 border-surface-200'
                      )}
                    >
                      {conv.status === 'active' ? 'Aktif' : 'Kapalı'}
                    </span>
                    <ChevronRight size={14} className="text-gray-600 group-hover:text-gray-400 transition-colors" />
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {selected && (
        <ConversationModal conv={selected} onClose={() => setSelected(null)} />
      )}
    </AppShell>
  )
}
