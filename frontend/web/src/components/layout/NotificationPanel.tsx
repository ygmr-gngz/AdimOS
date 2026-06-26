'use client'

import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import {
  Bell, X, CheckCheck, Trash2, Check, Video, FileText, Users, BarChart2,
  BookOpen, AlertTriangle, Clock, ChevronDown, ChevronUp, ExternalLink,
  GraduationCap, Search, Bot,
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import {
  notificationsService, type Notification, type FilterKey,
  FILTER_LABELS, filterNotif, groupByDate, getNotifColor, timeAgo,
} from '@/services/notifications.service'
import toast from 'react-hot-toast'

// ── İkon ──────────────────────────────────────────────────────
function NotifIcon({ type, size = 14 }: { type: string; size?: number }) {
  const cls = `shrink-0`
  if (type.startsWith('content'))       return <Video size={size} className={cls} />
  if (type.startsWith('document'))      return <FileText size={size} className={cls} />
  if (type.startsWith('lead') || type === 'followup_due') return <Users size={size} className={cls} />
  if (type === 'followup_due')          return <Clock size={size} className={cls} />
  if (type.startsWith('ceo'))           return <BarChart2 size={size} className={cls} />
  if (type.startsWith('agent'))         return <Bot size={size} className={cls} />
  if (type.startsWith('sgs'))           return <GraduationCap size={size} className={cls} />
  if (type === 'question_range_saved')  return <BookOpen size={size} className={cls} />
  if (type === 'quality_check_failed')  return <AlertTriangle size={size} className={cls} />
  return <Bell size={size} className={cls} />
}

// ── Renk Map ──────────────────────────────────────────────────
const COLOR_CLASSES = {
  green:  { border: 'border-l-green-500',  icon: 'text-green-400',  bg: 'bg-green-500/10' },
  red:    { border: 'border-l-red-500',    icon: 'text-red-400',    bg: 'bg-red-500/10' },
  yellow: { border: 'border-l-yellow-500', icon: 'text-yellow-400', bg: 'bg-yellow-500/10' },
  blue:   { border: 'border-l-blue-500',   icon: 'text-blue-400',   bg: 'bg-blue-500/10' },
  purple: { border: 'border-l-purple-500', icon: 'text-purple-400', bg: 'bg-purple-500/10' },
  gray:   { border: 'border-l-surface-300',icon: 'text-gray-500',   bg: '' },
}

// ── Bildirim Kartı ────────────────────────────────────────────
function NotifCard({
  n, onRead, onDelete,
}: {
  n: Notification
  onRead: (id: string) => void
  onDelete: (id: string) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const router = useRouter()
  const color = getNotifColor(n)
  const cls = COLOR_CLASSES[color]
  const msg = n.message || n.body || ''

  const handleAction = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!n.is_read) onRead(n.id)
    if (n.action_url) router.push(n.action_url)
  }

  return (
    <div
      className={`border-l-4 ${cls.border} ${n.is_read ? 'opacity-55' : ''} bg-surface-50 hover:bg-surface-100 transition-colors`}
    >
      {/* Ana satır */}
      <div
        className="flex items-start gap-3 px-4 py-3 cursor-pointer"
        onClick={() => { if (!n.is_read) onRead(n.id); setExpanded(x => !x) }}
      >
        {/* İkon */}
        <div className={`mt-0.5 p-1.5 rounded-lg ${cls.bg}`}>
          <span className={cls.icon}><NotifIcon type={n.type} size={13} /></span>
        </div>

        {/* İçerik */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <p className={`text-xs font-semibold leading-snug ${n.is_read ? 'text-gray-500' : 'text-gray-100'}`}>
              {n.title}
            </p>
            <div className="flex items-center gap-1 shrink-0">
              {!n.is_read && <div className="w-1.5 h-1.5 rounded-full bg-brand-400 mt-0.5" />}
              <span className="text-[10px] text-gray-600 whitespace-nowrap">{timeAgo(n.created_at)}</span>
            </div>
          </div>
          {msg && (
            <p className="text-xs text-gray-500 mt-0.5 leading-relaxed line-clamp-2">{msg}</p>
          )}
        </div>

        {/* Expand toggle */}
        <button
          onClick={e => { e.stopPropagation(); setExpanded(x => !x) }}
          className="mt-0.5 text-gray-600 hover:text-gray-300 shrink-0"
        >
          {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        </button>
      </div>

      {/* Detay alanı */}
      {expanded && (
        <div className="px-4 pb-3 pt-0 space-y-2 border-t border-surface-200/50">
          {/* Details JSONB */}
          {n.details && Object.keys(n.details).length > 0 && (
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 mt-2">
              {Object.entries(n.details).map(([k, v]) => (
                <div key={k} className="text-[10px]">
                  <span className="text-gray-600">{k}: </span>
                  <span className="text-gray-400">{String(v)}</span>
                </div>
              ))}
            </div>
          )}

          {/* Aksiyon butonları */}
          <div className="flex items-center gap-2 pt-1">
            {n.action_url && (
              <button
                onClick={handleAction}
                className="flex items-center gap-1 text-[11px] font-medium text-brand-400 hover:text-brand-300 transition-colors"
              >
                <ExternalLink size={11} /> İlgili sayfaya git
              </button>
            )}
            {!n.is_read && (
              <button
                onClick={e => { e.stopPropagation(); onRead(n.id) }}
                className="flex items-center gap-1 text-[11px] text-gray-600 hover:text-green-400 transition-colors"
              >
                <Check size={11} /> Okundu
              </button>
            )}
            <button
              onClick={e => { e.stopPropagation(); onDelete(n.id) }}
              className="ml-auto flex items-center gap-1 text-[11px] text-gray-700 hover:text-red-400 transition-colors"
            >
              <Trash2 size={11} /> Sil
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Ana Panel ─────────────────────────────────────────────────
interface Props {
  onClose: () => void
  onUnreadChange?: (count: number) => void
}

const FILTERS: FilterKey[] = ['all', 'unread', 'error', 'content', 'document', 'crm', 'agent', 'sgs']

function PanelContent({ onClose, onUnreadChange }: Props) {
  const [items, setItems] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<FilterKey>('all')
  const [search, setSearch] = useState('')
  const panelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    notificationsService.list()
      .then(({ notifications }) => {
        setItems(notifications)
        const unread = notifications.filter(n => !n.is_read).length
        onUnreadChange?.(unread)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [onUnreadChange])

  // Dışarı tıklama — sadece desktop
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) onClose()
    }
    const t = setTimeout(() => document.addEventListener('mousedown', handler), 50)
    return () => { clearTimeout(t); document.removeEventListener('mousedown', handler) }
  }, [onClose])

  const handleRead = async (id: string) => {
    await notificationsService.markRead(id)
    setItems(prev => {
      const next = prev.map(n => n.id === id ? { ...n, is_read: true } : n)
      onUnreadChange?.(next.filter(n => !n.is_read).length)
      return next
    })
  }

  const handleDelete = async (id: string) => {
    await notificationsService.deleteOne(id)
    setItems(prev => {
      const next = prev.filter(n => n.id !== id)
      onUnreadChange?.(next.filter(n => !n.is_read).length)
      return next
    })
  }

  const handleReadAll = async () => {
    await notificationsService.markAllRead()
    setItems(prev => prev.map(n => ({ ...n, is_read: true })))
    onUnreadChange?.(0)
    toast.success('Tümü okundu işaretlendi')
  }

  const handleClearRead = async () => {
    await notificationsService.clearRead()
    setItems(prev => {
      const next = prev.filter(n => !n.is_read)
      onUnreadChange?.(next.filter(n => !n.is_read).length)
      return next
    })
    toast.success('Okunanlar temizlendi')
  }

  // Filtre + arama
  const visible = items
    .filter(n => filterNotif(n, filter))
    .filter(n => {
      if (!search) return true
      const q = search.toLowerCase()
      return (
        n.title.toLowerCase().includes(q) ||
        (n.message || n.body || '').toLowerCase().includes(q)
      )
    })

  const groups = groupByDate(visible)
  const unread = items.filter(n => !n.is_read).length

  return (
    <>
      {/* Mobil overlay */}
      <div
        className="fixed inset-0 bg-black/50 z-[9998] md:hidden"
        onClick={onClose}
      />

      {/* Panel */}
      <div
        ref={panelRef}
        className={`
          fixed z-[9999] bg-surface-50 border border-surface-200 shadow-2xl flex flex-col
          /* Mobil: bottom sheet */
          bottom-0 left-0 right-0 rounded-t-2xl max-h-[85vh]
          /* Desktop: dropdown sağ üst */
          md:bottom-auto md:top-14 md:left-auto md:right-4 md:rounded-2xl md:w-[480px] md:max-h-[80vh]
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-surface-200 flex-shrink-0">
          <div className="flex items-center gap-2">
            <Bell size={14} className="text-brand-400" />
            <span className="text-sm font-bold text-white">Aktivite Merkezi</span>
            {unread > 0 && (
              <span className="text-xs bg-brand-600 text-white px-1.5 py-0.5 rounded-full font-bold min-w-[20px] text-center">
                {unread > 99 ? '99+' : unread}
              </span>
            )}
          </div>
          <div className="flex items-center gap-1">
            {unread > 0 && (
              <button onClick={handleReadAll} title="Tümünü okundu yap"
                className="p-1.5 text-gray-500 hover:text-green-400 transition-colors" >
                <CheckCheck size={14} />
              </button>
            )}
            <button onClick={handleClearRead} title="Okunanları temizle"
              className="p-1.5 text-gray-500 hover:text-red-400 transition-colors" >
              <Trash2 size={14} />
            </button>
            <button onClick={onClose}
              className="p-1.5 text-gray-500 hover:text-gray-200 transition-colors" >
              <X size={14} />
            </button>
          </div>
        </div>

        {/* Arama */}
        <div className="px-4 py-2 border-b border-surface-200 flex-shrink-0">
          <div className="flex items-center gap-2 bg-surface-100 rounded-lg px-3 py-1.5">
            <Search size={12} className="text-gray-600" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Ara..."
              className="flex-1 bg-transparent text-xs text-gray-300 placeholder-gray-600 outline-none"
            />
          </div>
        </div>

        {/* Filtreler */}
        <div className="px-4 py-2 flex gap-1.5 overflow-x-auto scrollbar-hide flex-shrink-0 border-b border-surface-200">
          {FILTERS.map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`text-[11px] font-medium px-2.5 py-1 rounded-full whitespace-nowrap transition-colors ${
                filter === f
                  ? 'bg-brand-600 text-white'
                  : 'bg-surface-100 text-gray-500 hover:text-gray-300'
              }`}
            >
              {FILTER_LABELS[f]}
            </button>
          ))}
        </div>

        {/* Liste */}
        <div className="flex-1 overflow-y-auto divide-y divide-surface-200/50">
          {loading ? (
            <div className="flex justify-center py-10">
              <svg className="animate-spin h-5 w-5 text-brand-400" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </div>
          ) : visible.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center px-8">
              <Bell size={28} className="text-gray-700 mb-3" />
              <p className="text-sm text-gray-500 font-medium">
                {search ? 'Arama sonucu bulunamadı' : filter === 'all' ? 'Henüz bildirim yok' : 'Bu kategoride bildirim yok'}
              </p>
            </div>
          ) : (
            groups.map(group => (
              <div key={group.label}>
                <div className="px-4 py-1.5 bg-surface-100/50 sticky top-0">
                  <span className="text-[10px] font-bold text-gray-600 uppercase tracking-wider">
                    {group.label}
                  </span>
                </div>
                {group.items.map(n => (
                  <NotifCard key={n.id} n={n} onRead={handleRead} onDelete={handleDelete} />
                ))}
              </div>
            ))
          )}
        </div>
      </div>
    </>
  )
}

// ── Portal Wrapper ────────────────────────────────────────────
export default function NotificationPanel(props: Props) {
  const [mounted, setMounted] = useState(false)
  useEffect(() => { setMounted(true) }, [])
  if (!mounted) return null
  return createPortal(<PanelContent {...props} />, document.body)
}
