'use client'

import { useState } from 'react'
import { Sparkles, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react'
import { dashboardService } from '@/services/dashboard.service'
import Button from '@/components/ui/Button'

interface DailyBriefCardProps {
  brief?: string
}

export default function DailyBriefCard({ brief: initialBrief }: DailyBriefCardProps) {
  const [brief, setBrief] = useState(initialBrief)
  const [isLoading, setIsLoading] = useState(false)
  const [expanded, setExpanded] = useState(false)

  const generateBrief = async () => {
    setIsLoading(true)
    try {
      const data = await dashboardService.getDailyBrief()
      setBrief(data.brief)
      setExpanded(true)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="bg-gradient-to-br from-brand-950/80 to-surface-50 rounded-xl p-5 border border-brand-600/20">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-brand-400" />
          <h3 className="text-sm font-semibold text-gray-200">CEO Günlük Özet</h3>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={generateBrief}
          isLoading={isLoading}
        >
          <RefreshCw size={14} />
          Üret
        </Button>
      </div>

      {brief ? (
        <div>
          <p className={`text-sm text-gray-400 leading-relaxed ${!expanded ? 'line-clamp-3' : ''}`}>
            {brief}
          </p>
          <button
            onClick={() => setExpanded(!expanded)}
            className="mt-2 text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1"
          >
            {expanded ? <><ChevronUp size={12} /> Daralt</> : <><ChevronDown size={12} /> Devamını Gör</>}
          </button>
        </div>
      ) : (
        <p className="text-sm text-gray-500 italic">
          Günlük özet henüz oluşturulmadı. &quot;Üret&quot; butonuna tıklayın.
        </p>
      )}
    </div>
  )
}
