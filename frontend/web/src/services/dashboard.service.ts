import apiClient from '@/lib/api-client'

export interface DashboardStats {
  total_documents: number
  indexed_documents: number
  failed_documents: number
  processing_documents: number
  total_leads: number
  new_leads: number
  followup_leads: number
  pending_content: number
  generating_content: number
  failed_content: number
  total_students: number
  published_content: number
  total_content: number
}

export interface DashboardData {
  stats: DashboardStats
  daily_brief?: string | null
  brief_generated_at?: string | null
  brief_title?: string | null
  recent_documents: Array<{
    id: string
    file_name: string
    status: string
    created_at: string
  }>
  recent_contents: Array<{
    id: string
    title: string
    content_type: string
    status: string
    created_at: string
  }>
  agent_statuses: Array<{
    agent_type: string
    status: string
    last_run?: string
  }>
}

export const dashboardService = {
  async getDashboard(): Promise<DashboardData> {
    const { data } = await apiClient.get('/dashboard')
    return data
  },

  async getDailyBrief(): Promise<{ brief: string; generated_at: string; title: string }> {
    const { data } = await apiClient.get('/dashboard/brief')
    return data
  },

  async generateBrief(): Promise<{ brief: string; generated_at: string; title: string }> {
    const { data } = await apiClient.post('/dashboard/brief/generate', {})
    return data
  },
}
