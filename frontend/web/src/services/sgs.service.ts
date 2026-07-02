import apiClient from '@/lib/api-client'

export const SGS_LESSON_GROUPS = {
  'Genel Dersler': ['Türkçe', 'Matematik', 'Tarih - Genel Kültür', 'İngilizce', 'Almanca'],
  'Hukuk': ['Ticaret Hukuku', 'Borçlar Hukuku', 'Vergi Hukuku', 'Meslek Hukuku', 'İş ve Sosyal Güvenlik Hukuku'],
  'Muhasebe': ['Finansal Muhasebe', 'Muhasebe Standartları', 'Muhasebe Bilgi Sistemi', 'Maliyet Muhasebesi', 'Mali Tablolar Analizi', 'Muhasebe Denetimi'],
  'Finans': ['Maliye', 'İktisat'],
} as const

export type SgsLessonGroup = keyof typeof SGS_LESSON_GROUPS

export const SGS_LESSONS = Object.values(SGS_LESSON_GROUPS).flat() as string[]

// Konu → doğru ders eşleştirmesi (AI hataları için referans ve manuel düzeltme rehberi)
export const TOPIC_LESSON_MAP: Readonly<Record<string, string>> = {
  // Türkçe
  'Anlam Bilgisi': 'Türkçe', 'Sözcükte Anlam': 'Türkçe', 'Cümlede Anlam': 'Türkçe',
  'Paragraf': 'Türkçe', 'Yazım Kuralları': 'Türkçe', 'Noktalama': 'Türkçe',
  'Anlatım Bozukluğu': 'Türkçe', 'Ses Bilgisi': 'Türkçe', 'Dil Bilgisi': 'Türkçe',
  // Matematik
  'Denklemler': 'Matematik', 'Fonksiyonlar': 'Matematik', 'Problemler': 'Matematik',
  'Sayılar': 'Matematik', 'Kümeler': 'Matematik', 'Oran Orantı': 'Matematik',
  'Olasılık': 'Matematik', 'Geometri': 'Matematik', 'Logaritma': 'Matematik',
  'Permütasyon': 'Matematik', 'Kombinasyon': 'Matematik', 'İstatistik': 'Matematik',
  // Tarih - Genel Kültür
  'Cumhuriyet Tarihi': 'Tarih - Genel Kültür', 'Atatürk İlkeleri': 'Tarih - Genel Kültür',
  'İnkılap Tarihi': 'Tarih - Genel Kültür', 'Osmanlı Tarihi': 'Tarih - Genel Kültür',
  'Genel Kültür': 'Tarih - Genel Kültür', 'Kurtuluş Savaşı': 'Tarih - Genel Kültür',
  // Finansal Muhasebe
  'Yevmiye': 'Finansal Muhasebe', 'Defter-i Kebir': 'Finansal Muhasebe',
  'Mizan': 'Finansal Muhasebe', 'Amortisman': 'Finansal Muhasebe',
  'Aktif / Pasif Hesaplar': 'Finansal Muhasebe', 'Dönem Sonu': 'Finansal Muhasebe',
  // Mali Tablolar Analizi
  'Bilanço': 'Mali Tablolar Analizi', 'Gelir Tablosu': 'Mali Tablolar Analizi',
  'Fon Akım Tablosu': 'Mali Tablolar Analizi', 'Nakit Akım Tablosu': 'Mali Tablolar Analizi',
  // Muhasebe Bilgi Sistemi
  'Tekdüzen Hesap Planı': 'Muhasebe Bilgi Sistemi',
  // Ticaret Hukuku
  'Tacir': 'Ticaret Hukuku', 'Ticari İşletme': 'Ticaret Hukuku',
  'Ticaret Unvanı': 'Ticaret Hukuku', 'İşletme Adı': 'Ticaret Hukuku',
  'Ticaret Sicili': 'Ticaret Hukuku', 'Haksız Rekabet': 'Ticaret Hukuku',
  // Borçlar Hukuku
  'Sözleşme': 'Borçlar Hukuku', 'Borç İlişkisi': 'Borçlar Hukuku',
  'Temerrüt': 'Borçlar Hukuku',
  // İş ve Sosyal Güvenlik Hukuku
  'İşçi': 'İş ve Sosyal Güvenlik Hukuku', 'SGK': 'İş ve Sosyal Güvenlik Hukuku',
  'İş Sözleşmesi': 'İş ve Sosyal Güvenlik Hukuku',
  // Vergi Hukuku
  'Gelir Vergisi': 'Vergi Hukuku', 'KDV': 'Vergi Hukuku',
  'Kurumlar Vergisi': 'Vergi Hukuku', 'Vergi Usul': 'Vergi Hukuku',
  // Maliye
  'Bütçe': 'Maliye', 'Kamu Maliyesi': 'Maliye',
  // İktisat
  'Para': 'İktisat', 'Talep': 'İktisat', 'Arz': 'İktisat',
  'Fiyat': 'İktisat', 'Piyasa': 'İktisat', 'Enflasyon': 'İktisat',
}

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
  document_name?: string
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

// ── Parse Pipeline Types ──────────────────────────────────────

export interface SgsParseResult {
  questions_created: number
  lessons: { lesson_name: string; count: number }[]
  analysis_id: string
}

export interface SgsQuestionStat {
  lesson_name: string
  lesson_group: string
  total: number
  topics: { topic: string; count: number }[]
  years: { year: string; count: number }[]
}

export interface SgsTopicDetail {
  topic: string
  total_questions: number
  lessons: { lesson_name: string; count: number }[]
  years: { year: string; count: number }[]
  frequency_pct: number
}

// ── Lesson Status ─────────────────────────────────────────────

export type SgsLessonStatus = 'no_range' | 'no_pdf' | 'no_questions' | 'ready'

export interface SgsAreaLesson {
  name: string
  expected: number
  found: number
  range_count: number
  status: SgsLessonStatus
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

  async bulkLinkRanges(analysisId: string): Promise<{ linked: number; pdf_name: string }> {
    const { data } = await apiClient.post('/sgs/ranges/bulk-link', { analysis_id: analysisId })
    return data
  },

  async parseQuestions(params: {
    analysis_id: string
    range_ids?: string[]
    document_id?: string
  }): Promise<SgsParseResult> {
    const { data } = await apiClient.post('/sgs/questions/parse-by-ranges', params)
    return data
  },

  async uploadAndAutoParse(file: File): Promise<{
    success: boolean
    document_id: string
    filename: string
    detected: { year?: string; period?: string; group?: string; language?: string }
    parsed: { total_questions: number; matched_ranges: number; unmatched_questions: number }
    lessons: { lesson_name: string; count: number }[]
    message: string
    error?: string
  }> {
    const form = new FormData()
    form.append('file', file)
    const { data } = await apiClient.post('/sgs/pdfs/upload-and-auto-parse', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 180_000,
    })
    return data
  },

  async getQuestionStats(filters?: { year?: string; area?: string; lesson?: string }): Promise<SgsQuestionStat[]> {
    const { data } = await apiClient.get('/sgs/question-stats', { params: filters ?? {} })
    return data.stats ?? []
  },

  async getTopicDetail(topic: string, lesson?: string): Promise<SgsTopicDetail> {
    const { data } = await apiClient.get('/sgs/topic-detail', {
      params: { topic, ...(lesson ? { lesson } : {}) },
    })
    return data
  },

  // GET /sgs/questions?topic=X&lesson=Y — backend bu endpoint'i implemente etmeli
  async getTopicQuestions(topic: string, lesson?: string): Promise<SgsQuestion[]> {
    const { data } = await apiClient.get('/sgs/questions', {
      params: { topic, ...(lesson ? { lesson } : {}) },
    })
    return data?.questions ?? []
  },

  // PATCH /sgs/questions/{id} — ders veya konu düzeltmesi
  async updateQuestionById(id: number, updates: { lesson_name?: string; topic?: string }): Promise<void> {
    await apiClient.patch(`/sgs/questions/${id}`, updates)
  },
}
