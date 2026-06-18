'use client'

import { useEffect, useRef, useState } from 'react'
import { Bell, Check, CheckCheck, Trash2, Video, Users, FileText, BarChart2, X } from 'lucide-react'
import { notificationsService, type Notification } from '@/services/notifications.service'
import toast from 'react-hot-toast'

const TYPE_ICONS: Record<string, React.ReactNode> = {
  content: <Video size={13} className="text-brand-400" />,
  content_error: <Video size={13} className="text-red-400" />,
  crm: <Users size={13} className="text-green-400" />,
  document: <FileText size={13} className="text-yellow-400" />,
  document_error: <FileText size={13} className="text-red-400" />,
  ceo: <BarChart2 size={13} className="text-purple-400" />,
}

function timeAgo(iso: string): string {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000
  if (diff < 60) return 'az önce'
  if (diff < 3600) return `${Math.floor(diff / 60)} dk önce`
  if (diff < 86400) return `${Math.floor(diff / 3600)} sa önce`
  return `${Math.floor(diff / 86400)} gün önce`
}

interface Props {
  onClose: () => void
}

export default function NotificationPanel({ onClose }: Props) {
  const [items, setItems] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const panelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    notificationsService.list()
      .then(({ notifications }) => setItems(notifications))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) onClose()
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [onClose])

  const handleRead = async (id: string) => {
    await notificationsService.markRead(id)
    setItems(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n))
  }

  const handleReadAll = async () => {
    await notificationsService.markAllRead()
    setItems(prev => prev.map(n => ({ ...n, is_read: true })))
    toast.success('Tümü okundu')
  }

  const handleClear = async () => {
    await notificationsService.clearRead()
    setItems(prev => prev.filter(n => !n.is_read))
    toast.success('Okunanlar temizlendi')
  }

  const unread = items.filter(n => !n.is_read).length

  return (
    <div
      ref={panelRef}
      className="absolute right-0 top-12 w-80 bg-surface-50 border border-surface-200 rounded-2xl shadow-2xl z-50 overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-surface-200">
        <div className="flex items-center gap-2">
          <Bell size={14} className="text-brand-400" />
          <span className="text-sm font-semibold text-white">Bildirimler</span>
          {unread > 0 && (
            <span className="text-xs bg-brand-600 text-white px-1.5 py-0.5 rounded-full font-bold">{unread}</span>
          )}
        </div>
        <div className="flex items-center gap-1">
          {unread > 0 && (
            <button onClick={handleReadAll} title="Tümünü oku" className="p-1.5 text-gray-500 hover:text-gray-300 transition-colors">
              <CheckCheck size={14} />
            </button>
          )}
          <button onClick={handleClear} title="Okunanları temizle" className="p-1.5 text-gray-500 hover:text-red-400 transition-colors">
            <Trash2 size={14} />
          </button>
          <button onClick={onClose} className="p-1.5 text-gray-500 hover:text-gray-300 transition-colors">
            <X size={14} />
          </button>
        </div>
      </div>

      {/* List */}
      <div className="max-h-80 overflow-y-auto">
        {loading ? (
          <div className="flex justify-center py-8">
            <svg className="animate-spin h-5 w-5 text-brand-400" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <Bell size={24} className="text-gray-600 mb-2" />
            <p className="text-xs text-gray-500">Bildirim yok</p>
          </div>
        ) : (
          items.map(n => (
            <div
              key={n.id}
              onClick={() => !n.is_read && handleRead(n.id)}
              className={`flex items-start gap-3 px-4 py-3 border-b border-surface-200 last:border-b-0 cursor-pointer transition-colors ${
                n.is_read ? 'opacity-60' : 'hover:bg-surface-100'
              }`}
            >
              <div className="mt-0.5 shrink-0">
                {TYPE_ICONS[n.type] ?? <Bell size={13} className="text-gray-400" />}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-1">
                  <p className={`text-xs font-medium leading-snug ${n.is_read ? 'text-gray-400' : 'text-gray-200'}`}>
                    {n.title}
                  </p>
                  {!n.is_read && (
                    <div className="w-1.5 h-1.5 rounded-full bg-brand-400 mt-1 shrink-0" />
                  )}
                </div>
                {n.body && (
                  <p className="text-xs text-gray-600 mt-0.5 leading-relaxed">{n.body}</p>
                )}
                <p className="text-xs text-gray-700 mt-1">{timeAgo(n.created_at)}</p>
              </div>
              {!n.is_read && (
                <button
                  onClick={e => { e.stopPropagation(); handleRead(n.id) }}
                  className="mt-0.5 p-1 text-gray-600 hover:text-green-400 transition-colors shrink-0"
                  title="Okundu"
                >
                  <Check size={12} />
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
