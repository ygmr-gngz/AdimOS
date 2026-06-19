'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { clsx } from 'clsx'
import {
  LayoutDashboard, BookOpen, Bot, Video, Users,
  GraduationCap, BarChart2, Globe, Settings, LogOut, X,
} from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'

const navItems = [
  { href: '/dashboard',   label: 'Kontrol Merkezi',   icon: LayoutDashboard },
  { href: '/knowledge',   label: 'Bilgi Merkezi',      icon: BookOpen },
  { href: '/agents',      label: 'Agent Ofisi',        icon: Bot },
  { href: '/automation',  label: 'İçerik Otomasyonu',  icon: Video },
  { href: '/crm',         label: 'Müşteri Yönetimi',   icon: Users },
  { href: '/academy',     label: 'SGS Akademi',        icon: GraduationCap },
  { href: '/website',     label: 'Web Sitesi',         icon: Globe },
  { href: '/reports',     label: 'Raporlar',           icon: BarChart2 },
]

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname()
  const router = useRouter()
  const { user, profile, signOut } = useAuth()

  const displayName = profile?.display_name ?? user?.email?.split('@')[0] ?? 'Kullanıcı'
  const roleLabel = profile?.role === 'admin' ? 'Admin' : 'Editör'

  // Rota değişince mobilde kapat
  useEffect(() => { onClose() }, [pathname]) // eslint-disable-line react-hooks/exhaustive-deps

  // ESC ile kapat
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  // Body scroll kilitle (mobilde açıkken)
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [isOpen])

  const handleSignOut = async () => {
    await signOut()
    router.push('/login')
  }

  const sidebarContent = (
    <aside className="w-64 flex flex-col h-full bg-surface-50 border-r border-surface-200">
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-5 border-b border-surface-200">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 bg-gradient-to-br from-brand-500 to-brand-700 shadow-lg">
            <span className="text-white font-black text-base tracking-tight">A</span>
          </div>
          <div>
            <span className="text-base font-bold tracking-tight">
              <span className="text-white">Adim</span>
              <span className="text-brand-400">OS</span>
            </span>
            <p className="text-xs text-gray-500 -mt-0.5">AI Operating System</p>
          </div>
        </div>
        {/* Mobil kapat butonu */}
        <button
          onClick={onClose}
          className="md:hidden p-1.5 text-gray-500 hover:text-gray-300 transition-colors"
        >
          <X size={18} />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-0.5">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href || pathname.startsWith(href + '/')
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
                isActive
                  ? 'bg-brand-600/20 text-brand-400 border border-brand-600/30'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-surface-100'
              )}
            >
              <Icon size={17} className={isActive ? 'text-brand-400' : ''} />
              {label}
            </Link>
          )
        })}
      </nav>

      {/* Alt kısım */}
      <div className="p-3 border-t border-surface-200">
        {profile?.role === 'admin' && (
          <Link
            href="/settings/users"
            className={clsx(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 mb-1',
              pathname === '/settings/users'
                ? 'bg-brand-600/20 text-brand-400 border border-brand-600/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-surface-100'
            )}
          >
            <Users size={17} />
            Kullanıcılar
          </Link>
        )}
        <Link
          href="/settings"
          className={clsx(
            'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 mb-1',
            pathname === '/settings'
              ? 'bg-brand-600/20 text-brand-400 border border-brand-600/30'
              : 'text-gray-400 hover:text-gray-200 hover:bg-surface-100'
          )}
        >
          <Settings size={17} />
          Ayarlar
        </Link>
        <div className="flex items-center gap-2.5 px-3 py-2 mt-1">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-brand-500/40 to-brand-700/40 border border-brand-600/30 flex items-center justify-center text-xs font-bold text-brand-400 flex-shrink-0">
            {displayName[0]?.toUpperCase() ?? 'U'}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium text-gray-300 truncate">{displayName}</p>
            <p className="text-xs text-gray-500 truncate">{roleLabel}</p>
          </div>
          <button
            onClick={handleSignOut}
            title="Çıkış Yap"
            className="p-1.5 rounded-lg text-gray-600 hover:text-red-400 hover:bg-red-500/10 transition-colors flex-shrink-0"
          >
            <LogOut size={14} />
          </button>
        </div>
      </div>
    </aside>
  )

  return (
    <>
      {/* ── Desktop: her zaman görünür, flex içinde ── */}
      <div className="hidden md:flex flex-shrink-0">
        {sidebarContent}
      </div>

      {/* ── Mobil: overlay + slide-in panel ── */}
      <div className={`md:hidden fixed inset-0 z-50 transition-all duration-300 ${isOpen ? 'visible' : 'invisible'}`}>
        {/* Backdrop */}
        <div
          className={`absolute inset-0 bg-black/60 transition-opacity duration-300 ${isOpen ? 'opacity-100' : 'opacity-0'}`}
          onClick={onClose}
        />
        {/* Panel */}
        <div className={`absolute inset-y-0 left-0 transition-transform duration-300 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
          {sidebarContent}
        </div>
      </div>
    </>
  )
}
