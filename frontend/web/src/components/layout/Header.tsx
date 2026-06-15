'use client'

import { Bell, User, Mic } from 'lucide-react'
import { usePathname } from 'next/navigation'

const pageTitles: Record<string, string> = {
  '/dashboard': 'Kontrol Merkezi',
  '/knowledge': 'Bilgi Merkezi',
  '/agents': 'Agent Ofisi',
  '/automation': 'İçerik Otomasyonu',
  '/crm': 'Müşteri Yönetimi',
  '/academy': 'SGS Akademi',
  '/website': 'Web Sitesi',
  '/reports': 'Raporlar',
  '/settings': 'Ayarlar',
  '/chat': 'Sohbet',
  '/voice': 'Sesli Asistan',
}

interface HeaderProps {
  onOpenAssistant: () => void
}

export default function Header({ onOpenAssistant }: HeaderProps) {
  const pathname = usePathname()
  const title = pageTitles[pathname] || 'AdimOS'

  return (
    <header className="h-14 bg-surface-50/80 backdrop-blur border-b border-surface-200 flex items-center justify-between px-6 flex-shrink-0">
      <span className="text-sm font-medium text-gray-500">{title}</span>

      <div className="flex items-center gap-2">
        <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-surface-200 text-gray-400 hover:text-gray-200 hover:border-surface-300 transition-colors text-xs font-medium">
          <Bell size={14} />
          Bildirimler
        </button>
        <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-surface-200 text-gray-400 hover:text-gray-200 hover:border-surface-300 transition-colors text-xs font-medium">
          <User size={14} />
          Profil
        </button>
        <button
          onClick={onOpenAssistant}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white transition-colors text-xs font-medium"
        >
          <Mic size={14} />
          Sesli Komut
        </button>
      </div>
    </header>
  )
}
