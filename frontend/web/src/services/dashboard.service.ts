import apiClient from '@/lib/api-client'

export interface DashboardStats {
  total_documents: number
  indexed_documents: number
  total_agent_runs: number
  total_leads: number
  total_students: number
  published_content: number
}

export interface DashboardData {
  stats: DashboardStats
  daily_brief?: string
  recent_documents: Array<{
    id: string
    file_name: string
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
  async getStats(): Promise<DashboardStats> {
    const { data } = await apiClient.get('/dashboard/stats')
    return data
  },

  async getDashboard(): Promise<DashboardData> {
    const { data } = await apiClient.get('/dashboard')
    return data
  },

  async getDailyBrief(): Promise<{ brief: string; generated_at: string }> {
    const { data } = await apiClient.get('/dashboard/brief')
    return data
  },
}
