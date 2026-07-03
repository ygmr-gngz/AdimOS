'use client'

import { useEffect, useState } from 'react'
import AppShell from '@/components/layout/AppShell'
import Button from '@/components/ui/Button'
import { BarChart2, RefreshCw, Clock, Loader2 } from 'lucide-react'
import { dashboardService } from '@/services/dashboard.service'
import toast from 'react-hot-toast'

interface Brief {
  brief: string | null
  generated_at: string | null
  title: string | null
}

export default function ReportsPage() {
  const [brief, setBrief] = useState<Brief | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  const loadBrief = async () => {
    setLoading(true)
    try {
      const data = await dashboardService.getDailyBrief()
      setBrief(data)
    } catch {
      setBrief({ brief: null, generated_at: null, title: null })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadBrief() }, [])

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      const data = await dashboardService.generateBrief()
      setBrief(data)
      toast.success('CEO özeti oluşturuldu')
    } catch {
      toast.error('Özet oluşturulamadı')
    } finally {
      setGenerating(false)
    }
  }

  const formattedDate = brief?.generated_at
    ? new Date(brief.generated_at).toLocaleString('tr-TR', {
        day: '2-digit', month: 'long', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      })
    : null

  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">CEO Agent Özeti</h2>
            <p className="text-sm text-gray-500 mt-1">Her sabah 08:00&apos;de otomatik oluşturulur</p>
          </div>
          <div className="flex items-center gap-2">
            <Button size="sm" variant="ghost" onClick={loadBrief} isLoading={loading}>
              <RefreshCw size={13} /> Yenile
            </Button>
            <Button size="sm" onClick={handleGenerate} isLoading={generating}>
              Şimdi Oluştur
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 size={28} className="animate-spin text-brand-400" />
          </div>
        ) : brief?.brief ? (
          <div className="bg-surface-50 border border-surface-200 rounded-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-surface-200 flex items-center justify-between">
              <p className="text-sm font-semibold text-gray-200">{brief.title ?? 'Günlük CEO Özeti'}</p>
              {formattedDate && (
                <span className="flex items-center gap-1.5 text-xs text-gray-500">
                  <Clock size={11} />
                  {formattedDate}
                </span>
              )}
            </div>
            <div className="px-6 py-5">
              <div className="prose prose-sm prose-invert max-w-none">
                {brief.brief.split('\n').map((line, i) => {
                  if (line.startsWith('## ')) {
                    return <h2 key={i} className="text-base font-bold text-white mt-4 mb-2 first:mt-0">{line.replace(/^## /, '').replace(/[*_]/g, '')}</h2>
                  }
                  if (line.startsWith('### ')) {
                    return <h3 key={i} className="text-sm font-semibold text-brand-300 mt-3 mb-1.5">{line.replace(/^### /, '')}</h3>
                  }
                  if (line.startsWith('---')) {
                    return <hr key={i} className="border-surface-300 my-3" />
                  }
                  if (line.match(/^\d+\./)) {
                    return <p key={i} className="text-sm text-gray-300 ml-4 mb-1 leading-relaxed">{line}</p>
                  }
                  if (line.trim() === '') {
                    return <div key={i} className="h-1" />
                  }
                  return <p key={i} className="text-sm text-gray-400 mb-1 leading-relaxed">{line}</p>
                })}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-16 bg-surface-50 border border-surface-200 rounded-2xl text-center">
            <BarChart2 size={32} className="text-gray-600 mb-3" />
            <p className="text-sm font-medium text-gray-400 mb-1">Henüz özet oluşturulmadı</p>
            <p className="text-xs text-gray-600 mb-4">
              CEO Agent her sabah 08:00&apos;de otomatik özet oluşturur
            </p>
            <Button size="sm" onClick={handleGenerate} isLoading={generating}>
              Şimdi Oluştur
            </Button>
          </div>
        )}
      </div>
    </AppShell>
  )
}
