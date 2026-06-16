import apiClient from '@/lib/api-client'

export type LeadStatus = 'new' | 'contacted' | 'qualified' | 'lost'

export interface Lead {
  id: string
  name: string
  email: string
  phone?: string
  status: LeadStatus
  source?: string
  notes?: string
  created_at: string
}

export interface LeadCreate {
  name: string
  email: string
  phone?: string
  status: LeadStatus
  source?: string
  notes?: string
}

export const crmService = {
  async list(): Promise<Lead[]> {
    const { data } = await apiClient.get('/crm')
    return Array.isArray(data) ? data : []
  },

  async create(lead: LeadCreate): Promise<Lead> {
    const { data } = await apiClient.post('/crm', lead)
    return data
  },

  async updateStatus(id: string, status: LeadStatus): Promise<Lead> {
    const { data } = await apiClient.patch(`/crm/${id}`, { status })
    return data
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/crm/${id}`)
  },
}
