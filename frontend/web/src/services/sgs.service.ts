import apiClient from '@/lib/api-client'

export interface SgsQuestion {
  id: number
  subject: string
  topic: string
  year?: string
  difficulty: 'kolay' | 'orta' | 'zor'
  question_text: string
  options: string[]
  correct_option: string
  explanation?: string
}

export interface SgsSubject {
  name: string
  question_count: number
  topics: string[]
}

export interface SgsVideoPlanItem {
  video_number: number
  title: string
  topic: string
  subject: string
  question_ids: number[]
  estimated_duration: string
  description: string
}

export interface SgsAnalysis {
  analysis_id?: string | null
  pdf_name: string
  total_questions: number
  subjects: SgsSubject[]
  questions: SgsQuestion[]
  video_plan: SgsVideoPlanItem[]
}

export interface SgsAnalysisMeta {
  id: string
  pdf_name: string
  total_questions: number
  subjects: SgsSubject[]
  video_plan: SgsVideoPlanItem[]
  status: string
  created_at: string
}

export const sgsService = {
  async analyzePdf(file: File): Promise<SgsAnalysis> {
    const form = new FormData()
    form.append('file', file)
    const { data } = await apiClient.post('/sgs/analyze', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120_000,
    })
    return data
  },

  async generateVideo(analysisId: string, videoPlanIndex: number): Promise<{
    content_id: string
    status: string
    title: string
    question_count: number
  }> {
    const { data } = await apiClient.post('/sgs/generate-video', {
      analysis_id: analysisId,
      video_plan_index: videoPlanIndex,
    })
    return data
  },

  async listAnalyses(): Promise<SgsAnalysisMeta[]> {
    const { data } = await apiClient.get('/sgs/analyses')
    return data ?? []
  },

  async getAnalysis(analysisId: string): Promise<SgsAnalysis & { id: string }> {
    const { data } = await apiClient.get(`/sgs/analyses/${analysisId}`)
    return data
  },

  async deleteAnalysis(analysisId: string): Promise<void> {
    await apiClient.delete(`/sgs/analyses/${analysisId}`)
  },
}
