'use client'

import { useEffect, useState } from 'react'
import AppShell from '@/components/layout/AppShell'
import StatCard from '@/components/dashboard/StatCard'
import DailyBriefCard from '@/components/dashboard/DailyBriefCard'
import { dashboardService, type DashboardData } from '@/services/dashboard.service'
import { FileText, Bot, Users, GraduationCap, Video, Database } from 'lucide-react'
import Badge from '@/components/ui/Badge'
import { useAuth } from '@/hooks/useAuth'
import { AGENT_STATUS_LABELS, DOCUMENT_STATUS_LABELS } from '@/lib/constants'

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

  const stats = data?.stats

  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in">
        <div>
          <h2 className="text-2xl font-bold text-white">
            Merhaba {displayName} 👋
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            {stats
              ? `Bugün sistemde ${stats.total_agent_runs} aktif görev ve ${stats.total_leads} bekleyen takip bulunuyor.`
              : 'AdimOS — Tüm sistem durumu burada'}
          </p>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          <StatCard label="Toplam Doküman" value={stats?.total_documents ?? 0} icon={FileText} color="blue" />
          <StatCard label="Bilgi Parçası" value={stats?.indexed_documents ?? 0} icon={Database} color="green" />
          <StatCard label="Aktif Agent" value={stats?.total_agent_runs ?? 0} icon={Bot} color="purple" />
          <StatCard label="Bekleyen Takip" value={stats?.total_leads ?? 0} icon={Users} color="orange" />
          <StatCard label="Sesli Oturum" value={0} icon={Video} color="blue" />
          <StatCard label="Öğrenci" value={stats?.total_students ?? 0} icon={GraduationCap} color="purple" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2">
            <DailyBriefCard brief={data?.daily_brief} />
          </div>
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-300">Agent Ofisi</h3>
            {data?.agent_statuses?.length ? (
              data.agent_statuses.map((a) => (
                <div key={a.agent_type} className="flex items-center justify-between p-3 bg-surface-50 rounded-lg border border-surface-200">
                  <span className="text-xs text-gray-400 capitalize">{a.agent_type.replace(/_/g, ' ')}</span>
                  <Badge
                    variant={a.status === 'running' ? 'warning' : a.status === 'completed' ? 'success' : a.status === 'failed' ? 'error' : 'default'}
                    dot
                  >
                    {AGENT_STATUS_LABELS[a.status] ?? a.status}
                  </Badge>
                </div>
              ))
            ) : (
              <div className="text-xs text-gray-600 p-3 bg-surface-50 rounded-lg border border-surface-200">
                Agent verisi bekleniyor...
              </div>
            )}
          </div>
        </div>

        {data?.recent_documents && data.recent_documents.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-300 mb-3">Son Yüklenen Dokümanlar</h3>
            <div className="space-y-2">
              {data.recent_documents.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between p-3 bg-surface-50 rounded-lg border border-surface-200">
                  <div className="flex items-center gap-2">
                    <FileText size={14} className="text-gray-500" />
                    <span className="text-xs text-gray-300 truncate max-w-xs">{doc.file_name}</span>
                  </div>
                  <div className="flex items-center gap-3">
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
      </div>
    </AppShell>
  )
}
