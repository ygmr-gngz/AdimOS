export type AgentStatus = 'idle' | 'running' | 'completed' | 'failed'

export type AgentType =
  | 'knowledge_agent'
  | 'voice_agent'
  | 'ceo_agent'
  | 'crm_agent'
  | 'followup_agent'
  | 'learning_agent'
  | 'automation_agent'

export interface Agent {
  id: AgentType
  name: string
  description: string
  status: AgentStatus
  icon: string
  last_run?: string
  run_count: number
}

export interface AgentRun {
  id: string
  agent_type: AgentType
  status: AgentStatus
  input: Record<string, unknown>
  output?: Record<string, unknown>
  error?: string
  started_at: string
  completed_at?: string
  duration_ms?: number
}

export interface AgentRunsResponse {
  runs: AgentRun[]
  total: number
}
