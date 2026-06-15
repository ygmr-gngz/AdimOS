import { LucideIcon, Brain, Mic, Briefcase, Users, UserCheck, BookOpen, Video } from 'lucide-react'
import Badge from '@/components/ui/Badge'
import type { Agent, AgentStatus } from '@/types/agent'
import { AGENT_STATUS_LABELS } from '@/lib/constants'

const agentIcons: Record<string, LucideIcon> = {
  knowledge_agent: Brain,
  voice_agent: Mic,
  ceo_agent: Briefcase,
  crm_agent: Users,
  followup_agent: UserCheck,
  learning_agent: BookOpen,
  automation_agent: Video,
}

const statusVariant: Record<AgentStatus, 'success' | 'warning' | 'error' | 'default'> = {
  idle: 'default',
  running: 'warning',
  completed: 'success',
  failed: 'error',
}

interface AgentCardProps {
  agent: Agent
}

export default function AgentCard({ agent }: AgentCardProps) {
  const Icon = agentIcons[agent.id] || Brain
  const isRunning = agent.status === 'running'

  return (
    <div className="bg-surface-50 rounded-xl p-5 border border-surface-200 hover:border-surface-300 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className={`p-2.5 rounded-lg ${isRunning ? 'bg-brand-600/20 animate-pulse-slow' : 'bg-surface-100'}`}>
          <Icon size={20} className={isRunning ? 'text-brand-400' : 'text-gray-400'} />
        </div>
        <Badge variant={statusVariant[agent.status]} dot>
          {AGENT_STATUS_LABELS[agent.status]}
        </Badge>
      </div>
      <h3 className="text-sm font-semibold text-gray-200 mb-1">{agent.name}</h3>
      <p className="text-xs text-gray-500 mb-3 line-clamp-2">{agent.description}</p>
      <div className="flex items-center justify-between text-xs text-gray-600">
        <span>{agent.run_count} çalışma</span>
        {agent.last_run && (
          <span>{new Date(agent.last_run).toLocaleDateString('tr-TR')}</span>
        )}
      </div>
    </div>
  )
}
