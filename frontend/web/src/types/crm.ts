export type LeadStatus = 'new' | 'contacted' | 'qualified' | 'proposal' | 'won' | 'lost'
export type LeadSource = 'instagram' | 'referral' | 'website' | 'phone' | 'other'

export interface Lead {
  id: string
  name: string
  email?: string
  phone?: string
  company?: string
  status: LeadStatus
  source: LeadSource
  score: number
  notes?: string
  tags: string[]
  created_at: string
  updated_at: string
  last_contact?: string
}

export interface CreateLeadRequest {
  name: string
  email?: string
  phone?: string
  company?: string
  source: LeadSource
  notes?: string
}

export interface LeadFollowUp {
  id: string
  lead_id: string
  message: string
  channel: 'email' | 'whatsapp' | 'phone'
  scheduled_at?: string
  sent_at?: string
  status: 'draft' | 'scheduled' | 'sent'
}
