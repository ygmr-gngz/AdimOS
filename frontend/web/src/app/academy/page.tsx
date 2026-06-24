'use client'

import { useCallback, useEffect, useState } from 'react'
import AppShell from '@/components/layout/AppShell'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import {
  GraduationCap, Upload, FileText, Play, ChevronDown,
  ChevronUp, Clock, BookOpen, Video, Trash2, RefreshCw, AlertTriangle, Edit2, List, Plus
} from 'lucide-react'
import { sgsService, SGS_LESSONS, SGS_DOCUMENT_TYPES, type SgsAnalysis, type SgsAnalysisMeta, type SgsQuestion, type SgsRange } from '@/services/sgs.service'
import toast from 'react-hot-toast'

type Phase = 'idle' | 'uploading' | 'done'

const DIFF_LABEL: Record<string, string> = { kolay: 'Kolay', orta: 'Orta', zor: 'Zor' }
const DIFF_COLOR: Record<string, string> = {
  kolay: 'text-green-400',
  orta: 'text-yellow-400',
  zor: 'text-red-400',
}

function DiffBadge({ diff }: { diff: string }) {
  return (
    <span className={`text-xs font-semibold ${DIFF_COLOR[diff] ?? 'text-gray-400'}`}>
      {DIFF_LABEL[diff] ?? diff}
    </span>
  )
}

function ConfidenceDot({ score }: { score?: number }) {
  if (score === undefined) return null
  const pct = Math.round(score * 100)
  const color = score >= 0.8 ? 'bg-green-400' : score >= 0.6 ? 'bg-yellow-400' : 'bg-red-400'
  return (
    <span className="flex items-center gap-1" title={`Ders güven: %${pct}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${color}`} />
      <span className="text-[10px] text-gray-600">%{pct}</span>
    </span>
  )
}

function VideoPlanCard({
  item, index, analysisId, onGenerate,
}: {
  item: SgsAnalysis['video_plan'][0]
  index: number
  analysisId: string | null | undefined
  onGenerate: (idx: number, title: string) => void
}) {
  const [open, setOpen] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [done, setDone] = useState(false)

  const handleGenerate = async () => {
    if (!analysisId) return
    setGenerating(true)
    try {
      await onGenerate(index, item.title)
      setDone(true)
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="bg-surface-50 rounded-xl border border-surface-200 overflow-hidden">
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-brand-600/20 flex items-center justify-center shrink-0">
            <span className="text-xs font-bold text-brand-400">{item.video_number}</span>
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-white truncate">{item.title}</p>
            <p className="text-xs text-gray-500">
              {item.subject} · {item.question_ids.length} soru · {item.estimated_duration}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {done ? (
            <Badge variant="success">Üretiliyor</Badge>
          ) : (
            <Button size="sm" variant="secondary" onClick={handleGenerate} isLoading={generating} disabled={!analysisId || generating}>
              <Play size={13} /> Üret
            </Button>
          )}
          <button onClick={() => setOpen(!open)} className="p-1.5 text-gray-500 hover:text-gray-300 transition-colors">
            {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </div>
      {open && (
        <div className="border-t border-surface-200 p-4 space-y-2">
          <p className="text-xs text-gray-400">{item.description}</p>
          <div className="flex flex-wrap gap-2 mt-2">
            <span className="text-xs bg-surface-200 text-gray-400 px-2 py-0.5 rounded-full">Konu: {item.topic}</span>
            <span className="text-xs bg-surface-200 text-gray-400 px-2 py-0.5 rounded-full">
              {item.question_ids.length} soru (ID: {item.question_ids.join(', ')})
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

function QuestionRow({
  question,
  analysisId,
  onLessonChange,
}: {
  question: SgsQuestion
  analysisId?: string | null
  onLessonChange?: (qId: number, newSubject: string) => void
}) {
  const [open, setOpen] = useState(false)
  const [editingLesson, setEditingLesson] = useState(false)
  const [saving, setSaving] = useState(false)
  const isUncertain = question.subject === 'Belirsiz' || (question.lesson_confidence !== undefined && question.lesson_confidence < 0.6)

  const handleLessonSave = async (newSubject: string) => {
    if (!analysisId || newSubject === question.subject) { setEditingLesson(false); return }
    setSaving(true)
    try {
      await sgsService.updateQuestionLesson(analysisId, question.id, newSubject)
      onLessonChange?.(question.id, newSubject)
      toast.success('Ders güncellendi')
    } catch {
      toast.error('Güncellenemedi')
    } finally {
      setSaving(false)
      setEditingLesson(false)
    }
  }

  return (
    <div className={`bg-surface-50 rounded-xl border overflow-hidden ${isUncertain ? 'border-yellow-500/30' : 'border-surface-200'}`}>
      <button onClick={() => setOpen(!open)} className="w-full text-left p-4 flex items-start gap-3">
        <span className="text-xs font-bold text-gray-600 shrink-0 mt-0.5">#{question.id}</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-gray-200 line-clamp-2">{question.question_text}</p>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            {/* Ders etiketi — tıklanabilir */}
            {editingLesson ? (
              <select
                autoFocus
                defaultValue={question.subject}
                onChange={e => handleLessonSave(e.target.value)}
                onBlur={() => setEditingLesson(false)}
                className="text-xs bg-surface-200 border border-brand-500/40 rounded px-1.5 py-0.5 text-gray-200 focus:outline-none"
                disabled={saving}
              >
                <option value="Belirsiz">Belirsiz</option>
                {SGS_LESSONS.map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            ) : (
              <button
                onClick={e => { e.stopPropagation(); setEditingLesson(true) }}
                className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded-full transition-colors group/lesson ${
                  isUncertain
                    ? 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/30'
                    : 'bg-surface-200 text-gray-400 hover:bg-surface-300'
                }`}
                title="Dersi düzelt"
              >
                {isUncertain && <AlertTriangle size={9} className="shrink-0" />}
                {question.subject}
                <Edit2 size={9} className="opacity-0 group-hover/lesson:opacity-100 transition-opacity" />
              </button>
            )}
            <span className="text-gray-700">·</span>
            <span className="text-xs text-gray-600">{question.topic}</span>
            {question.year && <><span className="text-gray-700">·</span><span className="text-xs text-gray-600">{question.year}</span></>}
            <span className="text-gray-700">·</span>
            <DiffBadge diff={question.difficulty} />
            <ConfidenceDot score={question.lesson_confidence} />
          </div>
          {question.lesson_reason && isUncertain && (
            <p className="text-[10px] text-yellow-600 mt-0.5">{question.lesson_reason}</p>
          )}
        </div>
        <span className="text-gray-600 shrink-0 mt-0.5">
          {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </span>
      </button>

      {open && (
        <div className="border-t border-surface-200 p-4 space-y-3">
          <div className="grid grid-cols-1 gap-1.5">
            {question.options.map((opt, i) => {
              const letter = 'ABCD'[i]
              const isCorrect = letter === question.correct_option?.toUpperCase()
              return (
                <div
                  key={i}
                  className={`flex items-start gap-2 p-2 rounded-lg text-sm ${
                    isCorrect ? 'bg-green-500/10 text-green-300' : 'text-gray-400'
                  }`}
                >
                  <span className={`font-bold shrink-0 ${isCorrect ? 'text-green-400' : 'text-gray-600'}`}>{letter})</span>
                  <span>{opt.replace(/^[ABCD]\)\s*/, '')}</span>
                  {isCorrect && <span className="ml-auto text-green-400 text-xs font-semibold">✓ Doğru</span>}
                </div>
              )
            })}
          </div>
          {question.explanation && (
            <div className="p-3 bg-surface-200 rounded-lg">
              <p className="text-xs text-gray-400 font-semibold mb-1">Açıklama</p>
              <p className="text-sm text-gray-300">{question.explanation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function RangesPanel() {
  const [ranges, setRanges] = useState<SgsRange[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({
    document_name: '',
    start_question_no: '',
    end_question_no: '',
    lesson_name: SGS_LESSONS[0] as string,
    notes: '',
  })

  useEffect(() => {
    sgsService.listRanges()
      .then(setRanges)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    const start = parseInt(form.start_question_no, 10)
    const end = parseInt(form.end_question_no, 10)
    if (!form.document_name.trim()) { toast.error('Belge adı boş olamaz'); return }
    if (!form.lesson_name) { toast.error('Ders seçilmedi'); return }
    if (isNaN(start) || start < 1) { toast.error('Başlangıç soru numarası geçersiz (min: 1)'); return }
    if (isNaN(end) || end < 1) { toast.error('Bitiş soru numarası geçersiz (min: 1)'); return }
    if (start > end) { toast.error(`Başlangıç (${start}) bitiş (${end}) değerinden büyük olamaz`); return }
    setSaving(true)
    try {
      const saved = await sgsService.saveRange({
        document_name: form.document_name.trim(),
        start_question_no: start,
        end_question_no: end,
        lesson_name: form.lesson_name,
        notes: form.notes.trim() || '',
      })
      setRanges(prev => [...prev, saved])
      setForm(f => ({ ...f, start_question_no: '', end_question_no: '', notes: '' }))
      toast.success('Aralık kaydedildi')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(msg ? `Hata: ${msg}` : 'Aralık kaydedilemedi — lütfen tekrar deneyin')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await sgsService.deleteRange(id)
      setRanges(prev => prev.filter(r => r.id !== id))
      toast.success('Aralık silindi')
    } catch {
      toast.error('Silinemedi')
    }
  }

  return (
    <div className="space-y-6">
      {/* Form */}
      <div className="bg-surface-50 rounded-xl border border-surface-200 p-5">
        <h3 className="text-sm font-semibold text-gray-200 mb-4 flex items-center gap-2">
          <Plus size={14} className="text-brand-400" /> Yeni Aralık Tanımla
        </h3>
        <form onSubmit={handleSave} className="space-y-4" noValidate>
          <div>
            <label className="text-xs font-medium text-gray-400 mb-1 block">Belge Adı</label>
            <input
              className="w-full bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500 placeholder-gray-600"
              placeholder="örn: 2026-1 SGS Çıkmış Sorular"
              value={form.document_name}
              onChange={e => setForm(f => ({ ...f, document_name: e.target.value }))}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-gray-400 mb-1 block">Başlangıç Sorusu</label>
              <input
                type="number" min={1}
                className="w-full bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="1"
                value={form.start_question_no}
                onChange={e => setForm(f => ({ ...f, start_question_no: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-400 mb-1 block">Bitiş Sorusu</label>
              <input
                type="number" min={1}
                className="w-full bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="20"
                value={form.end_question_no}
                onChange={e => setForm(f => ({ ...f, end_question_no: e.target.value }))}
              />
            </div>
          </div>
          <div>
            <label className="text-xs font-medium text-gray-400 mb-1 block">Ders</label>
            <select
              className="w-full bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
              value={form.lesson_name}
              onChange={e => setForm(f => ({ ...f, lesson_name: e.target.value }))}
            >
              {SGS_LESSONS.map(l => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium text-gray-400 mb-1 block">Not (isteğe bağlı)</label>
            <input
              className="w-full bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500 placeholder-gray-600"
              placeholder="örn: İlk 20 soru Türkçe bölümüne ait"
              value={form.notes}
              onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
            />
          </div>
          <Button type="submit" isLoading={saving} disabled={saving}>
            <Plus size={14} /> Kaydet
          </Button>
        </form>
      </div>

      {/* Tablo */}
      <div className="bg-surface-50 rounded-xl border border-surface-200 overflow-hidden">
        <div className="px-5 py-3 border-b border-surface-200 flex items-center gap-2">
          <List size={14} className="text-gray-500" />
          <span className="text-sm font-semibold text-gray-300">Kayıtlı Aralıklar ({ranges.length})</span>
        </div>
        {loading ? (
          <div className="p-8 text-center text-gray-600 text-sm">Yükleniyor...</div>
        ) : ranges.length === 0 ? (
          <div className="p-8 text-center text-gray-600 text-sm">Henüz aralık tanımlanmadı</div>
        ) : (
          <div className="divide-y divide-surface-200">
            {ranges.map(r => (
              <div key={r.id} className="flex items-center justify-between px-5 py-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-mono bg-surface-200 text-gray-300 px-2 py-0.5 rounded">
                      {r.start_question_no}–{r.end_question_no}
                    </span>
                    <span className="text-sm font-medium text-brand-300">{r.lesson_name}</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5 truncate">{r.document_name}{r.notes ? ` · ${r.notes}` : ''}</p>
                </div>
                <button
                  onClick={() => handleDelete(r.id)}
                  className="p-1.5 text-gray-600 hover:text-red-400 transition-colors shrink-0 ml-3"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function AnalysisResult({
  analysis, onGenerate, onLessonChange,
}: {
  analysis: SgsAnalysis
  onGenerate: (idx: number, title: string) => void
  onLessonChange: (qId: number, newSubject: string) => void
}) {
  const [tab, setTab] = useState<'plan' | 'questions'>('plan')
  const [subjFilter, setSubjFilter] = useState<string>('Tümü')

  const subjects = Array.from(new Set(analysis.questions.map(q => q.subject)))
  const uncertainCount = analysis.questions.filter(q =>
    q.subject === 'Belirsiz' || (q.lesson_confidence !== undefined && q.lesson_confidence < 0.6)
  ).length

  const filteredQ = subjFilter === 'Tümü'
    ? analysis.questions
    : subjFilter === 'Belirsiz'
    ? analysis.questions.filter(q => q.subject === 'Belirsiz' || (q.lesson_confidence !== undefined && q.lesson_confidence < 0.6))
    : analysis.questions.filter(q => q.subject === subjFilter)

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-surface-50 rounded-xl p-4 border border-surface-200 text-center">
          <p className="text-2xl font-bold text-white">{analysis.total_questions}</p>
          <p className="text-xs text-gray-500 mt-0.5">Toplam Soru</p>
        </div>
        <div className="bg-surface-50 rounded-xl p-4 border border-surface-200 text-center">
          <p className="text-2xl font-bold text-white">{analysis.subjects.length}</p>
          <p className="text-xs text-gray-500 mt-0.5">Ders</p>
        </div>
        <div className="bg-surface-50 rounded-xl p-4 border border-surface-200 text-center">
          <p className="text-2xl font-bold text-brand-400">{analysis.video_plan.length}</p>
          <p className="text-xs text-gray-500 mt-0.5">Planlanan Video</p>
        </div>
        <div className={`rounded-xl p-4 border text-center ${uncertainCount > 0 ? 'bg-yellow-500/5 border-yellow-500/30' : 'bg-surface-50 border-surface-200'}`}>
          <p className={`text-2xl font-bold ${uncertainCount > 0 ? 'text-yellow-400' : 'text-white'}`}>{uncertainCount}</p>
          <p className="text-xs text-gray-500 mt-0.5">Belirsiz Ders</p>
        </div>
      </div>

      {uncertainCount > 0 && (
        <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-xl flex items-start gap-2">
          <AlertTriangle size={14} className="text-yellow-400 mt-0.5 shrink-0" />
          <p className="text-xs text-yellow-300">
            <strong>{uncertainCount} soru</strong> için ders eşleşmesi belirsiz. Soru Bankası &rarr; &quot;Belirsiz&quot; filtresinden kontrol edip dersi düzeltebilirsiniz.
          </p>
        </div>
      )}

      <div className="flex gap-1 bg-surface-100 p-1 rounded-xl w-fit">
        {(['plan', 'questions'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              tab === t ? 'bg-surface-50 text-white shadow-sm' : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            {t === 'plan' ? `Video Planı (${analysis.video_plan.length})` : `Soru Bankası (${analysis.total_questions})`}
          </button>
        ))}
      </div>

      {tab === 'plan' && (
        <div className="space-y-3">
          {analysis.video_plan.map((item, idx) => (
            <VideoPlanCard key={idx} item={item} index={idx} analysisId={analysis.analysis_id} onGenerate={onGenerate} />
          ))}
        </div>
      )}

      {tab === 'questions' && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {['Tümü', ...(uncertainCount > 0 ? ['Belirsiz'] : []), ...subjects.filter(s => s !== 'Belirsiz')].map(s => (
              <button
                key={s}
                onClick={() => setSubjFilter(s)}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                  subjFilter === s
                    ? s === 'Belirsiz'
                      ? 'bg-yellow-500/20 border-yellow-500/40 text-yellow-300'
                      : 'bg-brand-600/20 border-brand-500/50 text-brand-300'
                    : 'bg-surface-100 border-surface-200 text-gray-500 hover:text-gray-300'
                }`}
              >
                {s}{s === 'Belirsiz' && ` (${uncertainCount})`}
              </button>
            ))}
          </div>

          <div className="space-y-2">
            {filteredQ.map(q => (
              <QuestionRow
                key={q.id}
                question={q}
                analysisId={analysis.analysis_id}
                onLessonChange={onLessonChange}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default function AcademyPage() {
  const [pageTab, setPageTab] = useState<'analyses' | 'ranges'>('analyses')
  const [phase, setPhase] = useState<Phase>('idle')
  const [analysis, setAnalysis] = useState<SgsAnalysis | null>(null)
  const [savedAnalyses, setSavedAnalyses] = useState<SgsAnalysisMeta[]>([])
  const [loadingList, setLoadingList] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [generatedTitles, setGeneratedTitles] = useState<string[]>([])
  const [uploadMeta, setUploadMeta] = useState({
    document_type: SGS_DOCUMENT_TYPES[0] as string,
    year: '',
    semester: '',
  })

  useEffect(() => {
    sgsService.listAnalyses()
      .then(setSavedAnalyses)
      .catch(() => {})
      .finally(() => setLoadingList(false))
  }, [])

  const handleFileChange = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setPhase('uploading')
    setError(null)
    setAnalysis(null)
    try {
      const result = await sgsService.analyzePdf(file, {
        document_type: uploadMeta.document_type,
        year: uploadMeta.year,
        semester: uploadMeta.semester,
      })
      setAnalysis(result)
      setPhase('done')
      const list = await sgsService.listAnalyses()
      setSavedAnalyses(list)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Bilinmeyen hata'
      setError(msg)
      setPhase('idle')
    }
    e.target.value = ''
  }, [uploadMeta])

  const handleLoadSaved = async (id: string) => {
    try {
      const data = await sgsService.getAnalysis(id)
      setAnalysis({ ...data, analysis_id: data.id })
      setPhase('done')
    } catch {
      setError('Analiz yüklenemedi')
    }
  }

  const handleDeleteSaved = async (id: string) => {
    try {
      await sgsService.deleteAnalysis(id)
      setSavedAnalyses(prev => prev.filter(a => a.id !== id))
      if (analysis?.analysis_id === id) { setAnalysis(null); setPhase('idle') }
    } catch {
      setError('Silinemedi')
    }
  }

  const handleGenerate = async (idx: number, title: string) => {
    if (!analysis?.analysis_id) return
    await sgsService.generateVideo(analysis.analysis_id, idx)
    setGeneratedTitles(prev => [...prev, title])
  }

  const handleLessonChange = (qId: number, newSubject: string) => {
    setAnalysis(prev => {
      if (!prev) return prev
      return {
        ...prev,
        questions: prev.questions.map(q =>
          q.id === qId ? { ...q, subject: newSubject, lesson_confidence: 1.0 } : q
        ),
      }
    })
  }

  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in">
        <div className="flex items-start justify-between flex-wrap gap-3">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <GraduationCap size={20} className="text-brand-400" />
              SGS Academy
            </h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Çıkmış soru PDF&apos;i yükle → otomatik video serisi planla → üret
            </p>
          </div>
          <div className="flex gap-1 bg-surface-100 p-1 rounded-xl">
            <button
              onClick={() => setPageTab('analyses')}
              className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                pageTab === 'analyses' ? 'bg-surface-50 text-white shadow-sm' : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              <BookOpen size={13} /> Analizler
            </button>
            <button
              onClick={() => setPageTab('ranges')}
              className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                pageTab === 'ranges' ? 'bg-surface-50 text-white shadow-sm' : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              <List size={13} /> Soru Aralıkları
            </button>
          </div>
        </div>

        {pageTab === 'ranges' && <RangesPanel />}

        {pageTab === 'analyses' && generatedTitles.length > 0 && (
          <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-xl">
            <p className="text-sm text-green-300 font-medium">
              {generatedTitles.length} video üretimi arka planda başladı. Otomasyon sayfasından takip edebilirsiniz.
            </p>
          </div>
        )}

        {pageTab === 'analyses' && phase !== 'done' && (
          <div className="space-y-3">
            {/* Metadata formu */}
            {phase === 'idle' && (
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-400 mb-1 block">Belge Türü</label>
                  <select
                    className="w-full bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    value={uploadMeta.document_type}
                    onChange={e => setUploadMeta(m => ({ ...m, document_type: e.target.value }))}
                  >
                    {SGS_DOCUMENT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-400 mb-1 block">Yıl</label>
                  <input
                    type="text"
                    placeholder="örn: 2025"
                    className="w-full bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500 placeholder-gray-600"
                    value={uploadMeta.year}
                    onChange={e => setUploadMeta(m => ({ ...m, year: e.target.value }))}
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-400 mb-1 block">Dönem</label>
                  <select
                    className="w-full bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    value={uploadMeta.semester}
                    onChange={e => setUploadMeta(m => ({ ...m, semester: e.target.value }))}
                  >
                    <option value="">Seçiniz</option>
                    <option value="1. Dönem">1. Dönem</option>
                    <option value="2. Dönem">2. Dönem</option>
                  </select>
                </div>
              </div>
            )}

            {/* Upload alanı */}
            <label
              htmlFor="sgs-pdf-input"
              className={`block border-2 border-dashed rounded-2xl p-10 text-center transition-all ${
                phase === 'uploading'
                  ? 'border-brand-500/30 cursor-not-allowed'
                  : 'border-surface-300 cursor-pointer hover:border-brand-500/50 hover:bg-brand-500/5'
              }`}
            >
              <input
                id="sgs-pdf-input"
                type="file"
                accept=".pdf,application/pdf"
                className="hidden"
                onChange={handleFileChange}
                disabled={phase === 'uploading'}
              />
              {phase === 'uploading' ? (
                <div className="flex flex-col items-center gap-3">
                  <svg className="animate-spin h-10 w-10 text-brand-400" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <p className="text-sm text-brand-300 font-medium">PDF analiz ediliyor...</p>
                  <p className="text-xs text-gray-500">Sorular çıkarılıyor, derslere ayrılıyor, video planı oluşturuluyor</p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <div className="w-16 h-16 rounded-2xl bg-brand-600/10 flex items-center justify-center">
                    <Upload size={28} className="text-brand-400" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-200">SGS soru bankası PDF&apos;i yükle</p>
                    <p className="text-xs text-gray-500 mt-1">
                      17 SGS dersine göre otomatik sınıflandırma · ders güven skoru · video planı
                    </p>
                  </div>
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-100 border border-surface-200 text-sm text-gray-300">
                    <FileText size={14} /> PDF Seç
                  </span>
                </div>
              )}
            </label>
          </div>
        )}

        {pageTab === 'analyses' && error && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {pageTab === 'analyses' && phase === 'done' && analysis && (
          <div className="space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <FileText size={16} className="text-brand-400" />
                <span className="text-sm font-semibold text-white">{analysis.pdf_name}</span>
                <Badge variant="success">Analiz Tamamlandı</Badge>
              </div>
              <Button size="sm" variant="ghost" onClick={() => { setPhase('idle'); setAnalysis(null) }}>
                <RefreshCw size={13} /> Yeni PDF
              </Button>
            </div>
            <AnalysisResult analysis={analysis} onGenerate={handleGenerate} onLessonChange={handleLessonChange} />
          </div>
        )}

        {pageTab === 'analyses' && !loadingList && savedAnalyses.length > 0 && phase !== 'done' && (
          <div>
            <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
              <Clock size={13} className="text-gray-500" />
              Önceki Analizler
            </h3>
            <div className="space-y-2">
              {savedAnalyses.map(a => (
                <div key={a.id} className="flex items-center justify-between p-4 bg-surface-50 rounded-xl border border-surface-200">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-lg bg-surface-200 flex items-center justify-center shrink-0">
                      <BookOpen size={14} className="text-gray-500" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm text-gray-200 font-medium truncate">{a.pdf_name}</p>
                      <p className="text-xs text-gray-500">
                        {a.document_type && <span className="text-brand-400/70">{a.document_type}</span>}
                        {a.year && <> · <span>{a.year}</span></>}
                        {a.semester && <> · <span>{a.semester}</span></>}
                        {' · '}{a.total_questions} soru · {a.video_plan.length} video planı ·{' '}
                        {new Date(a.created_at).toLocaleDateString('tr-TR')}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Button size="sm" variant="secondary" onClick={() => handleLoadSaved(a.id)}>
                      <Video size={13} /> Yükle
                    </Button>
                    <button onClick={() => handleDeleteSaved(a.id)} className="p-1.5 text-gray-600 hover:text-red-400 transition-colors">
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {pageTab === 'analyses' && !loadingList && savedAnalyses.length === 0 && phase === 'idle' && (
          <div className="flex flex-col items-center justify-center py-10 text-center text-gray-600 text-sm">
            <GraduationCap size={32} className="mb-3 text-gray-700" />
            <p>Henüz analiz yok. Yukarıdan bir PDF yükleyin.</p>
          </div>
        )}
      </div>
    </AppShell>
  )
}
