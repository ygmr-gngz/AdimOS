'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { clsx } from 'clsx'
import {
  LayoutDashboard,
  BookOpen,
  Bot,
  Video,
  Users,
  GraduationCap,
  BarChart2,
  Globe,
  Settings,
  LogOut,
} from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'

const navItems = [
  { href: '/dashboard', label: 'Kontrol Merkezi', icon: LayoutDashboard },
  { href: '/knowledge', label: 'Bilgi Merkezi', icon: BookOpen },
  { href: '/agents', label: 'Agent Ofisi', icon: Bot },
  { href: '/automation', label: 'İçerik Otomasyonu', icon: Video },
  { href: '/crm', label: 'Müşteri Yönetimi', icon: Users },
  { href: '/academy', label: 'SGS Akademi', icon: GraduationCap },
  { href: '/website', label: 'Web Sitesi', icon: Globe },
  { href: '/reports', label: 'Raporlar', icon: BarChart2 },
]

export default function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const { user, profile, signOut } = useAuth()

  const handleSignOut = async () => {
    await signOut()
    router.push('/login')
  }

  const displayName = profile?.display_name ?? user?.email?.split('@')[0] ?? 'Kullanıcı'
  const roleLabel = profile?.role === 'admin' ? 'Admin' : 'Editör'

  return (
    <aside className="w-64 flex-shrink-0 bg-surface-50 border-r border-surface-200 flex flex-col h-full">
      <div className="h-16 flex items-center px-5 border-b border-surface-200 gap-3">
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
            <Users size={17} className={pathname === '/settings/users' ? 'text-brand-400' : ''} />
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
          <Settings size={17} className={pathname === '/settings' ? 'text-brand-400' : ''} />
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
}
