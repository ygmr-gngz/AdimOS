'use client'

import { useState } from 'react'
import { Sparkles, RefreshCw, ChevronDown, ChevronUp, Clock } from 'lucide-react'
import { dashboardService } from '@/services/dashboard.service'
import Button from '@/components/ui/Button'

interface DailyBriefCardProps {
  brief?: string | null
  generatedAt?: string | null
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleString('tr-TR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return ''
  }
}

function BriefBody({ text }: { text: string }) {
  const lines = text.split('\n')
  return (
    <div className="space-y-1.5 text-sm">
      {lines.map((line, i) => {
        if (line.startsWith('## ')) {
          return (
            <h3 key={i} className="text-base font-semibold text-white mt-3 first:mt-0">
              {line.replace(/^##\s*/, '').replace(/[*#]/g, '').trim()}
            </h3>
          )
        }
        if (line.startsWith('### ')) {
          return (
            <h4 key={i} className="text-sm font-semibold text-brand-300 mt-2">
              {line.replace(/^###\s*/, '').replace(/[*#]/g, '').trim()}
            </h4>
          )
        }
        if (line.match(/^\d+\.\s/)) {
          return (
            <div key={i} className="flex gap-2 text-gray-300">
              <span className="text-brand-400 shrink-0">{line.match(/^\d+/)?.[0]}.</span>
              <span>{line.replace(/^\d+\.\s*/, '')}</span>
            </div>
          )
        }
        if (line.startsWith('* ') || line.startsWith('- ')) {
          return (
            <div key={i} className="flex gap-2 text-gray-300">
              <span className="text-brand-400 shrink-0 mt-0.5">•</span>
              <span>{line.replace(/^[*-]\s*/, '')}</span>
            </div>
          )
        }
        if (line.startsWith('---')) {
          return <hr key={i} className="border-surface-200 my-2" />
        }
        if (line.startsWith('*') && line.endsWith('*') && line.length > 2) {
          return <p key={i} className="text-xs text-gray-600 italic">{line.replace(/\*/g, '')}</p>
        }
        if (!line.trim()) return <div key={i} className="h-1" />
        return <p key={i} className="text-gray-300">{line}</p>
      })}
    </div>
  )
}

export default function DailyBriefCard({ brief: initialBrief, generatedAt: initialAt }: DailyBriefCardProps) {
  const [brief, setBrief] = useState<string | null | undefined>(initialBrief)
  const [generatedAt, setGeneratedAt] = useState<string | null | undefined>(initialAt)
  const [isLoading, setIsLoading] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleGenerate = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await dashboardService.generateBrief()
      setBrief(data.brief)
      setGeneratedAt(data.generated_at)
      setExpanded(true)
    } catch {
      setError('CEO özeti üretilemedi. Tekrar deneyin.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="bg-gradient-to-br from-brand-950/80 to-surface-50 rounded-xl p-5 border border-brand-600/20 h-full">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-brand-600/20 flex items-center justify-center">
            <Sparkles size={14} className="text-brand-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-200">CEO Günlük Özet</h3>
            {generatedAt && (
              <p className="text-xs text-gray-600 flex items-center gap-1">
                <Clock size={10} />
                {formatDate(generatedAt)}
              </p>
            )}
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleGenerate}
          isLoading={isLoading}
        >
          <RefreshCw size={13} />
          {brief ? 'Yenile' : 'Üret'}
        </Button>
      </div>

      {error && (
        <p className="text-xs text-red-400 mb-3 px-3 py-2 bg-red-500/10 rounded-lg border border-red-500/20">
          {error}
        </p>
      )}

      {brief ? (
        <div>
          <div className={`overflow-hidden transition-all duration-300 ${!expanded ? 'max-h-48' : ''}`}>
            <BriefBody text={brief} />
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="mt-3 text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1 transition-colors"
          >
            {expanded
              ? <><ChevronUp size={12} /> Daralt</>
              : <><ChevronDown size={12} /> Tamamını Gör</>}
          </button>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <div className="w-12 h-12 rounded-xl bg-surface-100 flex items-center justify-center mb-3">
            <Sparkles size={20} className="text-gray-600" />
          </div>
          <p className="text-sm text-gray-500 font-medium">Günlük özet hazır değil</p>
          <p className="text-xs text-gray-600 mt-1">
            &quot;Üret&quot; butonuna tıklayın — tüm sistem verileri analiz edilir.
          </p>
        </div>
      )}
    </div>
  )
}
