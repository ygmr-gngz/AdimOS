'use client'

import { useEffect, useRef, useState } from 'react'
import { Bell, User, Mic, Menu } from 'lucide-react'
import { usePathname } from 'next/navigation'
import NotificationPanel from './NotificationPanel'
import { notificationsService } from '@/services/notifications.service'

const pageTitles: Record<string, string> = {
  '/dashboard': 'Kontrol Merkezi',
  '/knowledge': 'Bilgi Merkezi',
  '/agents': 'Agent Ofisi',
  '/automation': 'İçerik Otomasyonu',
  '/crm': 'Müşteri Yönetimi',
  '/academy': 'SGS Akademi',
  '/website': 'Web Sitesi',
  '/reports': 'Raporlar',
  '/video': 'Video Prodüksiyon',
  '/settings': 'Ayarlar',
  '/chat': 'Sohbet',
  '/voice': 'Sesli Asistan',
}

interface HeaderProps {
  onOpenAssistant: () => void
  onOpenSidebar: () => void
}

export default function Header({ onOpenAssistant, onOpenSidebar }: HeaderProps) {
  const pathname = usePathname()
  const title = pageTitles[pathname] || 'AdimOS'
  const [notifOpen, setNotifOpen] = useState(false)
  const [unread, setUnread] = useState(0)
  const bellRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    notificationsService.list()
      .then(({ unread_count }) => setUnread(unread_count))
      .catch(() => {})

    const interval = setInterval(() => {
      notificationsService.list()
        .then(({ unread_count }) => setUnread(unread_count))
        .catch(() => {})
    }, 60_000)
    return () => clearInterval(interval)
  }, [])

  const handleOpenNotif = () => {
    setNotifOpen(true)
    setUnread(0)
  }

  return (
    <header className="h-14 bg-surface-50/80 backdrop-blur border-b border-surface-200 flex items-center justify-between px-4 md:px-6 flex-shrink-0">
      <div className="flex items-center gap-3">
        {/* Mobil hamburger */}
        <button
          onClick={onOpenSidebar}
          className="md:hidden p-1.5 text-gray-400 hover:text-gray-200 transition-colors"
          aria-label="Menüyü aç"
        >
          <Menu size={20} />
        </button>
        <span className="text-sm font-medium text-gray-500">{title}</span>
      </div>

      <div className="flex items-center gap-2">
        {/* Bildirim */}
        <div ref={bellRef}>
          <button
            onClick={handleOpenNotif}
            className="relative flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-surface-200 text-gray-400 hover:text-gray-200 hover:border-surface-300 transition-colors text-xs font-medium"
          >
            <Bell size={14} />
            <span className="hidden sm:inline">Bildirimler</span>
            {unread > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-brand-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                {unread > 9 ? '9+' : unread}
              </span>
            )}
          </button>
          {notifOpen && (
            <NotificationPanel
              onClose={() => setNotifOpen(false)}
              onUnreadChange={setUnread}
            />
          )}
        </div>

        <button className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-surface-200 text-gray-400 hover:text-gray-200 hover:border-surface-300 transition-colors text-xs font-medium">
          <User size={14} />
          Profil
        </button>
        <button
          onClick={onOpenAssistant}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white transition-colors text-xs font-medium"
        >
          <Mic size={14} />
          <span className="hidden sm:inline">Sesli Komut</span>
        </button>
      </div>
    </header>
  )
}
