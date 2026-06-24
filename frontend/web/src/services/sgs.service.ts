import apiClient from '@/lib/api-client'

export const SGS_LESSONS = [
  'Türkçe',
  'Matematik',
  'Tarih - Genel Kültür',
  'İngilizce',
  'Finansal Muhasebe',
  'Muhasebe Standartları',
  'Muhasebe Bilgi Sistemi',
  'Maliyet Muhasebesi',
  'Mali Tablolar Analizi',
  'Muhasebe Denetimi',
  'İktisat',
  'Maliye',
  'Meslek Hukuku',
  'İş ve Sosyal Güvenlik Hukuku',
  'Vergi Hukuku',
  'Ticaret Hukuku',
  'Borçlar Hukuku',
] as const

export type SgsLesson = typeof SGS_LESSONS[number] | 'Belirsiz'

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
  lesson_confidence?: number
  lesson_reason?: string
  original_subject?: string
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

export const SGS_DOCUMENT_TYPES = [
  'Çıkmış Sorular',
  'Deneme Sınavı',
  'Soru Bankası',
  'Cevap Anahtarı',
] as const

export type SgsDocumentType = typeof SGS_DOCUMENT_TYPES[number]

export interface SgsAnalysis {
  analysis_id?: string | null
  pdf_name: string
  document_type?: string
  year?: string
  semester?: string
  total_questions: number
  subjects: SgsSubject[]
  questions: SgsQuestion[]
  video_plan: SgsVideoPlanItem[]
}

export interface SgsAnalysisMeta {
  id: string
  pdf_name: string
  document_type?: string
  year?: string
  semester?: string
  total_questions: number
  subjects: SgsSubject[]
  video_plan: SgsVideoPlanItem[]
  status: string
  created_at: string
}

export interface SgsRange {
  id: string
  document_name: string
  document_id: string | null
  start_question_no: number
  end_question_no: number
  lesson_name: string
  notes: string | null
  created_at: string
}

export const sgsService = {
  async saveRange(payload: {
    document_name: string
    document_id?: string | null
    start_question_no: number
    end_question_no: number
    lesson_name: string
    notes?: string
  }): Promise<SgsRange> {
    const { data } = await apiClient.post('/sgs/ranges', payload)
    return data
  },

  async listRanges(documentName?: string): Promise<SgsRange[]> {
    const { data } = await apiClient.get('/sgs/ranges', {
      params: documentName ? { document_name: documentName } : undefined,
    })
    return data ?? []
  },

  async deleteRange(rangeId: string): Promise<void> {
    await apiClient.delete(`/sgs/ranges/${rangeId}`)
  },
  async analyzePdf(
    file: File,
    meta?: { document_type?: string; year?: string; semester?: string }
  ): Promise<SgsAnalysis> {
    const form = new FormData()
    form.append('file', file)
    if (meta?.document_type) form.append('document_type', meta.document_type)
    if (meta?.year) form.append('year', meta.year)
    if (meta?.semester) form.append('semester', meta.semester)
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

  async updateQuestionLesson(analysisId: string, questionId: number, newSubject: string): Promise<void> {
    await apiClient.patch(`/sgs/analyses/${analysisId}/question/${questionId}`, {
      new_subject: newSubject,
    })
  },
}
