'use client'

import { useEffect, useState } from 'react'
import AppShell from '@/components/layout/AppShell'
import AgentCard from '@/components/agents/AgentCard'
import type { Agent, AgentRun } from '@/types/agent'
import apiClient from '@/lib/api-client'
import Badge from '@/components/ui/Badge'
import { Clock } from 'lucide-react'

const defaultAgents: Agent[] = [
  { id: 'knowledge_agent',  name: 'Knowledge Agent',  description: 'Doküman işleme ve RAG tabanlı bilgi arama',       status: 'ready',   icon: 'brain',     run_count: 0 },
  { id: 'voice_agent',      name: 'Voice Agent',      description: 'Sesli soruları yanıtlar, ajanlara yönlendirir',    status: 'ready',   icon: 'mic',       run_count: 0 },
  { id: 'ceo_agent',        name: 'CEO Agent',        description: 'Her sabah 08:00 günlük yönetici özeti üretir',     status: 'running', icon: 'briefcase', run_count: 0 },
  { id: 'crm_agent',        name: 'CRM Agent',        description: 'Lead skorlama ve müşteri takibi yapar',            status: 'ready',   icon: 'users',     run_count: 0 },
  { id: 'followup_agent',   name: 'Follow-up Agent',  description: 'Her sabah 09:00 takip gereken leadleri listeler',  status: 'running', icon: 'usercheck', run_count: 0 },
  { id: 'learning_agent',   name: 'Learning Agent',   description: 'Öğrenci analizi ve öğrenme planı oluşturur',      status: 'ready',   icon: 'bookopen',  run_count: 0 },
  { id: 'automation_agent', name: 'Automation Agent', description: 'YouTube/Instagram içerik üretir ve yayınlar',     status: 'ready',   icon: 'video',     run_count: 0 },
]

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>(defaultAgents)
  const [recentRuns, setRecentRuns] = useState<AgentRun[]>([])

  useEffect(() => {
    apiClient.get('/agents').then((r) => setAgents(r.data)).catch(() => {})
    apiClient.get('/agents/runs?limit=10').then((r) => setRecentRuns(r.data.runs ?? [])).catch(() => {})
  }, [])

  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in">
        <div>
          <h2 className="text-xl font-bold text-white mb-1">Agent Ofisi</h2>
          <p className="text-sm text-gray-500">Tüm AI agent&apos;larının durumunu takip edin</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {agents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>

        {recentRuns.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-300 mb-3">Son Çalışmalar</h3>
            <div className="space-y-2">
              {recentRuns.map((run) => (
                <div key={run.id} className="flex items-center gap-4 p-3 bg-surface-50 rounded-lg border border-surface-200">
                  <Clock size={14} className="text-gray-500 flex-shrink-0" />
                  <span className="text-xs text-gray-400 flex-1">{run.agent_type.replace('_', ' ')}</span>
                  <span className="text-xs text-gray-600">{new Date(run.started_at).toLocaleString('tr-TR')}</span>
                  {run.duration_ms && (
                    <span className="text-xs text-gray-600">{(run.duration_ms / 1000).toFixed(1)}s</span>
                  )}
                  <Badge variant={run.status === 'completed' ? 'success' : run.status === 'failed' ? 'error' : run.status === 'running' ? 'warning' : 'default'}>
                    {run.status}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  )
}
