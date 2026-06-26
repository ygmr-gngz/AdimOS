import apiClient from '@/lib/api-client'

export const SGS_LESSON_GROUPS = {
  'Genel Dersler': ['Türkçe', 'Matematik', 'Tarih - Genel Kültür', 'İngilizce'],
  'Hukuk': ['Ticaret Hukuku', 'Borçlar Hukuku', 'Vergi Hukuku', 'Meslek Hukuku', 'İş ve Sosyal Güvenlik Hukuku'],
  'Muhasebe': ['Finansal Muhasebe', 'Muhasebe Standartları', 'Muhasebe Bilgi Sistemi', 'Maliyet Muhasebesi', 'Mali Tablolar Analizi', 'Muhasebe Denetimi'],
  'Finans': ['Maliye', 'İktisat'],
} as const

export type SgsLessonGroup = keyof typeof SGS_LESSON_GROUPS

export const SGS_LESSONS = Object.values(SGS_LESSON_GROUPS).flat() as string[]

export function getLessonGroup(lesson: string): SgsLessonGroup | null {
  for (const [group, lessons] of Object.entries(SGS_LESSON_GROUPS)) {
    if ((lessons as readonly string[]).includes(lesson)) return group as SgsLessonGroup
  }
  return null
}

export type SgsLesson = string

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

export interface SgsAreaLesson {
  name: string
  expected: number
  found: number
  range_count: number
}

export interface SgsArea {
  name: string
  expected_total: number
  found_total: number
  discrepancy: number
  status: 'ok' | 'warning' | 'missing'
  lessons: SgsAreaLesson[]
}

export interface SgsTopicAnalysis {
  total: number
  top_topics: { topic: string; count: number }[]
  lesson_breakdown?: { lesson: string; count: number }[]
  year_breakdown: { year: string; count: number }[]
  data_source: 'ranges' | 'ai'
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

  async getTopicAnalysis(params: {
    lesson?: string
    group?: string
    year?: string
  }): Promise<{
    lesson: string | null
    group: string | null
    year_filter: string | null
    total: number
    top_topics: { topic: string; count: number }[]
    lesson_breakdown: { lesson: string; count: number }[]
    year_breakdown: { year: string; count: number }[]
    sample_questions: SgsQuestion[]
  }> {
    const { data } = await apiClient.get('/sgs/topic-analysis', { params })
    return data
  },

  async generateTopicVideo(params: {
    lesson: string
    topic: string
    year?: string
    max_questions?: number
  }): Promise<{ content_id: string; status: string; title: string; question_count: number }> {
    const { data } = await apiClient.post('/sgs/generate-topic-video', params)
    return data
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

  async getAreas(year?: string): Promise<SgsArea[]> {
    const { data } = await apiClient.get('/sgs/areas', { params: year ? { year } : undefined })
    return data.areas ?? []
  },

  async getAreaTopicAnalysis(area: string, year?: string): Promise<SgsTopicAnalysis> {
    const { data } = await apiClient.get(`/sgs/areas/${encodeURIComponent(area)}/topic-analysis`, {
      params: year ? { year } : undefined,
    })
    return data
  },

  async getLessonTopicAnalysis(lesson: string, year?: string): Promise<SgsTopicAnalysis> {
    const { data } = await apiClient.get(`/sgs/lessons/${encodeURIComponent(lesson)}/topic-analysis`, {
      params: year ? { year } : undefined,
    })
    return data
  },
}
