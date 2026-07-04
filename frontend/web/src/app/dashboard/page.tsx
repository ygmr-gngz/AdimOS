'use client'

import { useEffect, useState } from 'react'
import AppShell from '@/components/layout/AppShell'
import DailyBriefCard from '@/components/dashboard/DailyBriefCard'
import { dashboardService, type DashboardData } from '@/services/dashboard.service'
import Link from 'next/link'
import {
  FileText, Users, Video, Database, AlertCircle,
  Clock, CheckCircle2, TrendingUp, GraduationCap,
  BookOpen, Film, ArrowRight,
} from 'lucide-react'
import Badge from '@/components/ui/Badge'
import { useAuth } from '@/hooks/useAuth'
import { DOCUMENT_STATUS_LABELS } from '@/lib/constants'

function KpiCard({
  label, value, sub, icon: Icon, color, alert,
}: {
  label: string
  value: number
  sub?: string
  icon: React.ElementType
  color: 'blue' | 'green' | 'orange' | 'red' | 'purple' | 'brand'
  alert?: boolean
}) {
  const colorMap: Record<string, string> = {
    blue:   'bg-blue-500/10 text-blue-400',
    green:  'bg-green-500/10 text-green-400',
    orange: 'bg-orange-500/10 text-orange-400',
    red:    'bg-red-500/10 text-red-400',
    purple: 'bg-purple-500/10 text-purple-400',
    brand:  'bg-brand-500/10 text-brand-400',
  }
  return (
    <div className={`relative bg-surface-50 rounded-xl p-4 border ${alert && value > 0 ? 'border-red-500/30' : 'border-surface-200'}`}>
      {alert && value > 0 && (
        <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-red-500 animate-pulse" />
      )}
      <div className={`w-8 h-8 rounded-lg ${colorMap[color]} flex items-center justify-center mb-3`}>
        <Icon size={16} />
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{label}</p>
      {sub && <p className="text-xs text-gray-600 mt-1">{sub}</p>}
    </div>
  )
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const { user } = useAuth()

  useEffect(() => {
    dashboardService.getDashboard()
      .then(setData)
      .catch(() => {})
      .finally(() => setIsLoading(false))
  }, [])

  const displayName = user?.user_metadata?.full_name
    ?? user?.email?.split('@')[0]
    ?? 'Yağmur'

  if (isLoading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-full">
          <div className="flex flex-col items-center gap-3">
            <svg className="animate-spin h-8 w-8 text-brand-400" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p className="text-sm text-gray-500">Yükleniyor...</p>
          </div>
        </div>
      </AppShell>
    )
  }

  const s = data?.stats

  const alerts: string[] = []
  if (s && s.failed_documents > 0) alerts.push(`${s.failed_documents} belge hatalı`)
  if (s && s.failed_content > 0) alerts.push(`${s.failed_content} içerik başarısız`)
  if (s && s.followup_leads > 0) alerts.push(`${s.followup_leads} müşteri takip bekliyor`)

  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in">

        {/* Başlık */}
        <div>
          <h2 className="text-2xl font-bold text-white">Merhaba, {displayName}</h2>
          <p className="text-sm text-gray-500 mt-1">
            {alerts.length > 0
              ? `Dikkat: ${alerts.join(' · ')}`
              : 'Tüm sistemler çalışıyor.'}
          </p>
        </div>

        {/* Hızlı Akışlar */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Bilgi Merkezi özet kartı — PDF yükleme için modüle yönlendir */}
          <Link href="/knowledge" className="group relative bg-surface-50 border border-surface-200 hover:border-blue-500/40 rounded-xl p-4 transition-all duration-150 hover:bg-blue-500/5">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center mb-3">
              <BookOpen size={16} />
            </div>
            <p className="text-sm font-semibold text-white">Bilgi Merkezi</p>
            <p className="text-xs text-gray-500 mt-0.5">
              {s?.indexed_documents
                ? <><span className="text-blue-400 font-medium">{s.indexed_documents}</span> doküman işlendi</>
                : 'Doküman yükle ve yönet'}
            </p>
            <ArrowRight size={13} className="absolute top-4 right-4 text-gray-600 group-hover:text-blue-400 transition-colors" />
          </Link>

          <Link href="/video" className="group relative bg-surface-50 border border-surface-200 hover:border-brand-500/40 rounded-xl p-4 transition-all duration-150 hover:bg-brand-500/5">
            <div className="w-8 h-8 rounded-lg bg-brand-500/10 text-brand-400 flex items-center justify-center mb-3">
              <Film size={16} />
            </div>
            <p className="text-sm font-semibold text-white">Video Üret</p>
            <p className="text-xs text-gray-500 mt-0.5">Konu anlatımı veya soru çözümü</p>
            <ArrowRight size={13} className="absolute top-4 right-4 text-gray-600 group-hover:text-brand-400 transition-colors" />
          </Link>

          <Link href="/video" className="group relative bg-surface-50 border border-surface-200 hover:border-amber-500/40 rounded-xl p-4 transition-all duration-150 hover:bg-amber-500/5">
            {s && s.pending_content > 0 && (
              <span className="absolute top-3 right-3 w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            )}
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center mb-3">
              <Clock size={16} />
            </div>
            <p className="text-sm font-semibold text-white">Onay Bekleyen</p>
            <p className="text-xs text-gray-500 mt-0.5">
              {s?.pending_content
                ? <><span className="text-amber-400 font-medium">{s.pending_content}</span> video inceleme bekliyor</>
                : 'İnceleme bekleyen video yok'}
            </p>
          </Link>
        </div>

        {/* KPI Izgarası */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
          <KpiCard label="İşlenen Belge"  value={s?.indexed_documents ?? 0}   icon={Database}      color="green" />
          <KpiCard label="Toplam İçerik"  value={s?.total_content ?? 0}       icon={Video}         color="brand" />
          <KpiCard label="Onay Bekleyen"  value={s?.pending_content ?? 0}     icon={Clock}         color="orange" />
          <KpiCard label="Yeni Lead"      value={s?.new_leads ?? 0}           icon={TrendingUp}    color="blue" />
          <KpiCard label="Takip Bekleyen" value={s?.followup_leads ?? 0}      icon={Users}         color="purple" />
          <KpiCard label="Yayınlanan"     value={s?.published_content ?? 0}   icon={CheckCircle2}  color="green" />
          <KpiCard label="Hatalı Belge"   value={s?.failed_documents ?? 0}    icon={AlertCircle}   color="red"   alert />
          <KpiCard label="Hatalı İçerik" value={s?.failed_content ?? 0}      icon={AlertCircle}   color="red"   alert />
          <KpiCard label="Öğrenci"        value={s?.total_students ?? 0}      icon={GraduationCap} color="purple" />
          <KpiCard label="Toplam Lead"    value={s?.total_leads ?? 0}         icon={Users}         color="blue" />
        </div>

        {/* CEO Özet — Ana Kart */}
        <DailyBriefCard
          brief={data?.daily_brief}
          generatedAt={data?.brief_generated_at}
        />

        {/* Alt Satır: Son Belgeler + Son İçerikler */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

          {data?.recent_documents && data.recent_documents.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                <Database size={13} className="text-gray-500" />
                Son Yüklenen Belgeler
              </h3>
              <div className="space-y-2">
                {data.recent_documents.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between p-3 bg-surface-50 rounded-lg border border-surface-200">
                    <div className="flex items-center gap-2 min-w-0">
                      <FileText size={13} className="text-gray-500 shrink-0" />
                      <span className="text-xs text-gray-300 truncate">{doc.file_name}</span>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-xs text-gray-600">{new Date(doc.created_at).toLocaleDateString('tr-TR')}</span>
                      <Badge variant={doc.status === 'indexed' ? 'success' : doc.status === 'failed' ? 'error' : 'warning'}>
                        {DOCUMENT_STATUS_LABELS[doc.status] ?? doc.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {data?.recent_contents && data.recent_contents.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                <Video size={13} className="text-gray-500" />
                Son Üretilen İçerikler
              </h3>
              <div className="space-y-2">
                {data.recent_contents.map((c) => (
                  <div key={c.id} className="flex items-center justify-between p-3 bg-surface-50 rounded-lg border border-surface-200">
                    <div className="flex items-center gap-2 min-w-0">
                      <Video size={13} className="text-gray-500 shrink-0" />
                      <span className="text-xs text-gray-300 truncate">{c.title || c.content_type}</span>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-xs text-gray-600">{new Date(c.created_at).toLocaleDateString('tr-TR')}</span>
                      <Badge variant={
                        c.status === 'published' ? 'success'
                        : c.status === 'failed' ? 'error'
                        : c.status === 'pending_approval' ? 'warning'
                        : 'default'
                      }>
                        {c.status === 'published' ? 'Yayında'
                          : c.status === 'failed' ? 'Hata'
                          : c.status === 'pending_approval' ? 'Onay Bekliyor'
                          : c.status === 'generating' ? 'Üretiliyor'
                          : c.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>
    </AppShell>
  )
}
