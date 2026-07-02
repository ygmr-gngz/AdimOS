'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import AppShell from '@/components/layout/AppShell'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import {
  GraduationCap, Upload, FileText, Play, ChevronDown,
  ChevronUp, Clock, BookOpen, Video, Trash2, RefreshCw, AlertTriangle, Edit2, List, Plus, BarChart2,
  CheckCircle2, X, Layers
} from 'lucide-react'
import { sgsService, SGS_LESSONS, SGS_LESSON_GROUPS, SGS_DOCUMENT_TYPES, type SgsAnalysis, type SgsAnalysisMeta, type SgsQuestion, type SgsRange, type SgsArea, type SgsTopicAnalysis } from '@/services/sgs.service'
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
                {Object.entries(SGS_LESSON_GROUPS).map(([group, lessons]) => (
                  <optgroup key={group} label={group}>
                    {lessons.map(l => <option key={l} value={l}>{l}</option>)}
                  </optgroup>
                ))}
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



// ── Alan + Soru Aralıkları Birleşik Paneli ───────────────────

// ── Toplu Aralık Oluşturma Modalı ─────────────────────────────

type BulkQplMode = '5' | '6' | 'custom'

interface BulkEntry {
  lesson_name: string
  area: string
  start_question_no: number
  end_question_no: number
  count: number
  conflict?: string
}

const BULK_AREAS = ['Hukuk', 'Muhasebe', 'Finans', 'Genel Dersler', 'Tümü'] as const

function BulkRangeModal({
  pdfOptions,
  existingRanges,
  onClose,
  onSaved,
}: {
  pdfOptions: SgsAnalysisMeta[]
  existingRanges: SgsRange[]
  onClose: () => void
  onSaved: () => void
}) {
  const [step, setStep] = useState<'config' | 'preview'>('config')
  const [analysisId, setAnalysisId] = useState(pdfOptions[0]?.id ?? '')
  const [selectedArea, setSelectedArea] = useState<string>('Hukuk')
  const [startNo, setStartNo] = useState(1)
  const [qplMode, setQplMode] = useState<BulkQplMode>('6')
  const [customCounts, setCustomCounts] = useState<Record<string, number>>({})
  const [preview, setPreview] = useState<BulkEntry[]>([])
  const [saving, setSaving] = useState(false)

  const selectedPdf = pdfOptions.find(a => a.id === analysisId)

  const currentLessons: readonly string[] = selectedArea === 'Tümü'
    ? Object.values(SGS_LESSON_GROUPS).flat()
    : (SGS_LESSON_GROUPS[selectedArea as keyof typeof SGS_LESSON_GROUPS] ?? [])

  function buildEntries(): BulkEntry[] {
    const areas = selectedArea === 'Tümü'
      ? Object.keys(SGS_LESSON_GROUPS)
      : [selectedArea]
    const entries: BulkEntry[] = []
    let cur = startNo

    for (const area of areas) {
      const lessons = SGS_LESSON_GROUPS[area as keyof typeof SGS_LESSON_GROUPS] ?? []
      for (const lesson of lessons) {
        const count = qplMode === 'custom'
          ? (customCounts[lesson] ?? 6)
          : parseInt(qplMode)
        const start = cur
        const end = cur + count - 1
        cur += count

        const conflict = existingRanges.find(r =>
          r.lesson_name === lesson &&
          r.start_question_no <= end &&
          r.end_question_no >= start
        )
        entries.push({
          lesson_name: lesson,
          area,
          start_question_no: start,
          end_question_no: end,
          count,
          conflict: conflict
            ? `${conflict.start_question_no}–${conflict.end_question_no} ile çakışıyor`
            : undefined,
        })
      }
    }
    return entries
  }

  function handlePreview() {
    if (!analysisId) { toast.error('Lütfen bir PDF seçin'); return }
    if (startNo < 1) { toast.error('Başlangıç numarası geçersiz'); return }
    setPreview(buildEntries())
    setStep('preview')
  }

  async function handleSave() {
    if (!selectedPdf) return
    setSaving(true)
    const toSave = preview.filter(e => !e.conflict)
    try {
      for (const entry of toSave) {
        await sgsService.saveRange({
          document_id: analysisId,
          document_name: selectedPdf.pdf_name,
          lesson_name: entry.lesson_name,
          start_question_no: entry.start_question_no,
          end_question_no: entry.end_question_no,
        })
      }
      const skipped = preview.length - toSave.length
      toast.success(
        `${toSave.length} aralık oluşturuldu` +
        (skipped > 0 ? `, ${skipped} çakışma atlandı` : '')
      )
      onSaved()
    } catch {
      toast.error('Kaydetme sırasında hata oluştu')
    } finally {
      setSaving(false)
    }
  }

  const totalQuestions = currentLessons.reduce((s, l) =>
    s + (qplMode === 'custom' ? (customCounts[l] ?? 6) : parseInt(qplMode)), 0)
  const cleanCount = preview.filter(e => !e.conflict).length
  const conflictCount = preview.filter(e => e.conflict).length

  const SEL = 'w-full bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500'
  const INP = 'w-full bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500 text-center'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="bg-surface-50 border border-surface-200 rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-surface-200 shrink-0">
          <div className="flex items-center gap-2">
            <Layers size={15} className="text-brand-400" />
            <span className="text-sm font-bold text-gray-100">Toplu Aralık Oluştur</span>
            <span className="text-xs text-gray-600 bg-surface-200 px-2 py-0.5 rounded">
              {step === 'config' ? 'Yapılandır' : 'Önizle ve Kaydet'}
            </span>
          </div>
          <div className="flex items-center gap-3">
            {step === 'preview' && (
              <button onClick={() => setStep('config')} className="text-xs text-gray-500 hover:text-gray-300 transition-colors">
                ← Düzenle
              </button>
            )}
            <button onClick={onClose} className="text-gray-500 hover:text-gray-200 transition-colors">
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {step === 'config' ? (
            <>
              {/* PDF */}
              <div>
                <label className="text-xs font-medium text-gray-400 mb-1.5 block">PDF Seç</label>
                {pdfOptions.length === 0 ? (
                  <p className="text-xs text-yellow-400 py-2">Önce &quot;Analizler&quot; sekmesinden PDF yükleyin.</p>
                ) : (
                  <select className={SEL} value={analysisId} onChange={e => setAnalysisId(e.target.value)}>
                    <option value="">— PDF seçin —</option>
                    {pdfOptions.map(a => (
                      <option key={a.id} value={a.id}>
                        {a.pdf_name}{a.year ? ` (${a.year}${a.semester ? ' · ' + a.semester : ''})` : ''}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* Alan */}
              <div>
                <label className="text-xs font-medium text-gray-400 mb-1.5 block">Alan / Şablon</label>
                <div className="flex flex-wrap gap-2">
                  {BULK_AREAS.map(a => (
                    <button
                      key={a}
                      onClick={() => setSelectedArea(a)}
                      className={`text-xs py-1.5 px-3 rounded-lg border transition-colors ${
                        selectedArea === a
                          ? 'bg-brand-600/20 border-brand-500/40 text-brand-300'
                          : 'bg-surface-100 border-surface-200 text-gray-400 hover:text-gray-200'
                      }`}
                    >
                      {a}
                      {a !== 'Tümü' && (
                        <span className="ml-1 text-gray-600">
                          ({SGS_LESSON_GROUPS[a as keyof typeof SGS_LESSON_GROUPS]?.length ?? 0} ders)
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Başlangıç + QPL */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-medium text-gray-400 mb-1.5 block">Başlangıç Soru No</label>
                  <input
                    type="number" min={1}
                    className={INP}
                    value={startNo}
                    onChange={e => setStartNo(parseInt(e.target.value) || 1)}
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-400 mb-1.5 block">Her Dersten</label>
                  <div className="flex gap-2">
                    {(['5', '6', 'custom'] as const).map(m => (
                      <button
                        key={m}
                        onClick={() => setQplMode(m)}
                        className={`flex-1 text-xs py-2 rounded-lg border transition-colors ${
                          qplMode === m
                            ? 'bg-brand-600/20 border-brand-500/40 text-brand-300'
                            : 'bg-surface-100 border-surface-200 text-gray-400 hover:text-gray-200'
                        }`}
                      >
                        {m === 'custom' ? 'Özel' : `${m} soru`}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Özel dağılım */}
              {qplMode === 'custom' && (
                <div className="bg-surface-100 rounded-xl border border-surface-200 p-4 space-y-2">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-xs font-medium text-gray-400">Ders Başına Soru Sayısı</p>
                    <button
                      onClick={() => setCustomCounts({})}
                      className="text-[11px] text-gray-600 hover:text-gray-400 transition-colors"
                    >
                      Hepsini 6 yap
                    </button>
                  </div>
                  {currentLessons.map(lesson => (
                    <div key={lesson} className="flex items-center gap-3">
                      <span className="text-xs text-gray-400 flex-1 min-w-0 truncate">{lesson}</span>
                      <input
                        type="number" min={1} max={99}
                        className="w-16 bg-surface-50 border border-surface-300 rounded-lg px-2 py-1.5 text-sm text-gray-100 text-center focus:outline-none focus:ring-1 focus:ring-brand-500"
                        value={customCounts[lesson] ?? 6}
                        onChange={e => setCustomCounts(prev => ({
                          ...prev,
                          [lesson]: parseInt(e.target.value) || 1,
                        }))}
                      />
                      <span className="text-xs text-gray-600 w-8">soru</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Özet */}
              <div className="bg-brand-500/5 border border-brand-500/20 rounded-xl px-4 py-3 flex items-center justify-between">
                <span className="text-xs text-gray-400">
                  {currentLessons.length} ders · Başlangıç: <span className="text-gray-200 font-mono">{startNo}</span>
                </span>
                <span className="text-sm font-semibold text-brand-300">{totalQuestions} soru toplam</span>
              </div>
            </>
          ) : (
            <>
              {/* Preview header */}
              <div className="flex items-center justify-between">
                <p className="text-xs text-gray-500">
                  <span className="font-medium text-gray-300">{selectedPdf?.pdf_name}</span>
                  {' · '}{selectedArea}
                </p>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-green-400">{cleanCount} yeni</span>
                  {conflictCount > 0 && (
                    <span className="text-xs text-orange-400 flex items-center gap-1">
                      <AlertTriangle size={11} /> {conflictCount} çakışma
                    </span>
                  )}
                </div>
              </div>

              <div className="bg-surface-100 rounded-xl overflow-hidden border border-surface-200">
                {preview.map((entry, i) => (
                  <div
                    key={i}
                    className={`flex items-center gap-3 px-4 py-2.5 border-b border-surface-200 last:border-0 ${
                      entry.conflict ? 'opacity-40' : ''
                    }`}
                  >
                    <span className="font-mono text-xs text-brand-300 bg-brand-500/10 px-2 py-0.5 rounded w-20 text-center shrink-0">
                      {entry.start_question_no}–{entry.end_question_no}
                    </span>
                    <span className="text-sm text-gray-300 flex-1 truncate">{entry.lesson_name}</span>
                    <span className="text-xs text-gray-600 shrink-0">{entry.count} soru</span>
                    {entry.conflict ? (
                      <span className="text-[10px] text-orange-400 shrink-0 max-w-[120px] text-right">{entry.conflict}</span>
                    ) : (
                      <CheckCircle2 size={12} className="text-green-500 shrink-0" />
                    )}
                  </div>
                ))}
              </div>

              {conflictCount > 0 && (
                <p className="text-xs text-orange-400/80">
                  Çakışan aralıklar atlanacak. Sadece {cleanCount} yeni aralık kaydedilecek.
                </p>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-surface-200 shrink-0">
          <button onClick={onClose} className="text-sm text-gray-500 hover:text-gray-300 px-4 py-2 transition-colors">
            İptal
          </button>
          {step === 'config' ? (
            <Button onClick={handlePreview}>
              Önizle →
            </Button>
          ) : (
            <Button onClick={handleSave} isLoading={saving} disabled={saving || cleanCount === 0}>
              <CheckCircle2 size={14} /> {cleanCount} Aralık Kaydet
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Otomatik Parse Upload ─────────────────────────────────────

// ── Alan Analizi Paneli ────────────────────────────────────────

function AreaAnalysisPanel() {
  const [areas, setAreas] = useState<SgsArea[]>([])
  const [areasLoading, setAreasLoading] = useState(true)
  const [yearFilter, setYearFilter] = useState('')
  const [selectedArea, setSelectedArea] = useState<string | null>(null)
  const [selectedLesson, setSelectedLesson] = useState<string | null>(null)
  const [topicAnalysis, setTopicAnalysis] = useState<SgsTopicAnalysis | null>(null)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [generatingTopic, setGeneratingTopic] = useState<string | null>(null)

  const [selectedTopic, setSelectedTopic] = useState<string | null>(null)

  // Toplu aralık modal
  const [showBulkModal, setShowBulkModal] = useState(false)

  // Aralık yönetimi state
  const [ranges, setRanges] = useState<SgsRange[]>([])
  const [rangesLoading, setRangesLoading] = useState(true)
  const [showRangeForm, setShowRangeForm] = useState(false)
  const [savingRange, setSavingRange] = useState(false)
  const [pdfOptions, setPdfOptions] = useState<SgsAnalysisMeta[]>([])
  const [rangeForm, setRangeForm] = useState({
    document_id: '',
    document_name: '',
    start_question_no: '',
    end_question_no: '',
    lesson_name: SGS_LESSONS[0] as string,
    notes: '',
  })

  const loadAreas = async (year?: string) => {
    setAreasLoading(true)
    try {
      const data = await sgsService.getAreas(year || undefined)
      setAreas(data)
    } catch {
      toast.error('Alan özeti alınamadı')
    } finally {
      setAreasLoading(false)
    }
  }

  useEffect(() => {
    loadAreas()
    sgsService.listRanges()
      .then(setRanges)
      .catch(() => {})
      .finally(() => setRangesLoading(false))
    sgsService.listAnalyses()
      .then(setPdfOptions)
      .catch(() => {})
  }, [])

  const handleYearFilter = (y: string) => {
    setYearFilter(y)
    setTopicAnalysis(null)
  }

  const handleAreaClick = (area: string) => {
    if (selectedArea === area) {
      setSelectedArea(null)
      setSelectedLesson(null)
      setTopicAnalysis(null)
    } else {
      setSelectedArea(area)
      setSelectedLesson(null)
      setTopicAnalysis(null)
    }
  }

  const handleAnalyze = async (areaName: string, lessonName?: string) => {
    setAnalysisLoading(true)
    setTopicAnalysis(null)
    try {
      const result = lessonName
        ? await sgsService.getLessonTopicAnalysis(lessonName, yearFilter || undefined)
        : await sgsService.getAreaTopicAnalysis(areaName, yearFilter || undefined)
      setTopicAnalysis(result)
    } catch {
      toast.error('Konu analizi alınamadı')
    } finally {
      setAnalysisLoading(false)
    }
  }

  const handleGenerateVideo = async (lesson: string, topic: string) => {
    setGeneratingTopic(topic)
    try {
      const res = await sgsService.generateTopicVideo({ lesson, topic, year: yearFilter || undefined, max_questions: 5 })
      toast.success(`"${res.title}" video üretimi başladı (${res.question_count} soru)`)
    } catch {
      toast.error('Video üretimi başlatılamadı')
    } finally {
      setGeneratingTopic(null)
    }
  }

  const handleSaveRange = async (e: React.FormEvent) => {
    e.preventDefault()
    const start = parseInt(rangeForm.start_question_no, 10)
    const end = parseInt(rangeForm.end_question_no, 10)
    if (!rangeForm.document_id) { toast.error('Lütfen bir PDF seçin'); return }
    if (isNaN(start) || start < 1) { toast.error('Başlangıç soru numarası geçersiz'); return }
    if (isNaN(end) || end < start) { toast.error(`Bitiş (${end}) başlangıçtan (${start}) küçük olamaz`); return }
    setSavingRange(true)
    try {
      const saved = await sgsService.saveRange({
        document_name: rangeForm.document_name,
        document_id: rangeForm.document_id,
        start_question_no: start,
        end_question_no: end,
        lesson_name: rangeForm.lesson_name,
        notes: rangeForm.notes.trim() || '',
      })
      setRanges(prev => [...prev, saved])
      setRangeForm(f => ({ ...f, start_question_no: '', end_question_no: '', notes: '' }))
      toast.success('Aralık kaydedildi')
      setShowRangeForm(false)
      loadAreas(yearFilter || undefined)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(msg ? `Hata: ${msg}` : 'Aralık kaydedilemedi')
    } finally {
      setSavingRange(false)
    }
  }

  const handleDeleteRange = async (id: string) => {
    try {
      await sgsService.deleteRange(id)
      setRanges(prev => prev.filter(r => r.id !== id))
      loadAreas(yearFilter || undefined)
      toast.success('Aralık silindi')
    } catch {
      toast.error('Silinemedi')
    }
  }

  const handleDeleteByArea = async (area: string) => {
    const lessons = SGS_LESSON_GROUPS[area as keyof typeof SGS_LESSON_GROUPS] ?? []
    const toDelete = ranges.filter(r => (lessons as readonly string[]).includes(r.lesson_name))
    if (toDelete.length === 0) { toast.error('Bu alana ait aralık yok'); return }
    if (!window.confirm(`${area} alanına ait ${toDelete.length} aralık silinecek. Emin misin?`)) return
    try {
      for (const r of toDelete) await sgsService.deleteRange(r.id)
      setRanges(prev => prev.filter(r => !toDelete.some(d => d.id === r.id)))
      loadAreas(yearFilter || undefined)
      toast.success(`${toDelete.length} aralık silindi`)
    } catch {
      toast.error('Silme sırasında hata oluştu')
    }
  }

  const currentArea = areas.find(a => a.name === selectedArea)

  return (
    <div className="space-y-6">
      {/* Yıl Filtresi */}
      <div className="flex items-end gap-3 flex-wrap">
        <div className="max-w-[180px]">
          <label className="text-xs font-medium text-gray-400 mb-1 block">Yıl Filtresi</label>
          <input
            type="text"
            placeholder="örn: 2024 (isteğe bağlı)"
            value={yearFilter}
            onChange={e => handleYearFilter(e.target.value)}
            className="w-full bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500 placeholder-gray-600"
          />
        </div>
        <Button size="sm" variant="secondary" onClick={() => loadAreas(yearFilter || undefined)} isLoading={areasLoading}>
          <RefreshCw size={13} /> Yenile
        </Button>
      </div>

      {/* Alan Kartları */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {areasLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 bg-surface-100 rounded-xl border border-surface-200 animate-pulse" />
          ))
        ) : areas.map(area => {
          const color = GROUP_COLORS[area.name] ?? 'text-gray-400 bg-surface-100 border-surface-200'
          const isActive = selectedArea === area.name
          const hasData = area.expected_total > 0
          const hasDiscrepancy = area.discrepancy > 0 && hasData

          return (
            <button
              key={area.name}
              onClick={() => handleAreaClick(area.name)}
              className={`p-3 rounded-xl border text-left transition-all ${
                isActive ? color : 'bg-surface-100 border-surface-200 hover:border-surface-300'
              }`}
            >
              <div className="flex items-start justify-between">
                <p className={`text-sm font-semibold ${isActive ? color.split(' ')[0] : 'text-gray-300'}`}>
                  {area.name}
                </p>
                {hasData && (
                  hasDiscrepancy
                    ? <AlertTriangle size={11} className="text-yellow-400 shrink-0 mt-0.5" />
                    : <CheckCircle2 size={11} className="text-green-400 shrink-0 mt-0.5" />
                )}
              </div>
              <p className="text-lg font-bold text-white mt-1">{area.expected_total}</p>
              <p className="text-[10px] text-gray-500 mt-0.5">
                {hasData
                  ? hasDiscrepancy
                    ? `${area.found_total} bulundu · ${area.discrepancy} eksik`
                    : `${area.found_total} soru eşleşti`
                  : 'Aralık tanımlanmamış'}
              </p>
            </button>
          )
        })}
      </div>

      {/* Seçili Alan Detayı */}
      {currentArea && (
        <div className="bg-surface-50 rounded-xl border border-surface-200 overflow-hidden">
          <div className="px-5 py-3 border-b border-surface-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={`text-sm font-semibold ${GROUP_COLORS[currentArea.name]?.split(' ')[0] ?? 'text-gray-200'}`}>
                {currentArea.name}
              </span>
              <span className="text-xs text-gray-500">·</span>
              <span className="text-xs text-gray-500">{currentArea.expected_total} beklenen soru</span>
            </div>
            <Button
              size="sm"
              onClick={() => { setSelectedLesson(null); handleAnalyze(currentArea.name) }}
              isLoading={analysisLoading && !selectedLesson}
            >
              <BarChart2 size={12} /> Alan Analizi
            </Button>
          </div>
          <div className="divide-y divide-surface-200">
            {currentArea.lessons.map(lesson => {
              const isActive = selectedLesson === lesson.name
              return (
                <div
                  key={lesson.name}
                  className={`flex items-center justify-between px-5 py-3 cursor-pointer transition-colors ${
                    isActive ? 'bg-brand-600/10' : 'hover:bg-surface-100'
                  }`}
                  onClick={() => {
                    const next = isActive ? null : lesson.name
                    setSelectedLesson(next)
                    setTopicAnalysis(null)
                    if (next) handleAnalyze(currentArea.name, next)
                  }}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="min-w-0">
                      <p className={`text-sm font-medium truncate ${isActive ? 'text-brand-300' : 'text-gray-300'}`}>
                        {lesson.name}
                      </p>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        {lesson.found > 0 ? (
                          <span className="text-[10px] text-green-500">{lesson.found} soru</span>
                        ) : (
                          <span className="text-[10px] text-gray-600">Henüz veri yok</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {lesson.range_count > 0 && (
                      <span className="text-[10px] bg-surface-200 text-gray-500 px-1.5 py-0.5 rounded">
                        {lesson.range_count} aralık
                      </span>
                    )}
                    <ChevronDown size={13} className={`text-gray-600 transition-transform ${isActive ? 'rotate-180' : ''}`} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Konu Analizi Sonuçları */}
      {(analysisLoading || topicAnalysis) && (
        <div className="space-y-4">
          {analysisLoading ? (
            <div className="flex justify-center py-10">
              <svg className="animate-spin h-6 w-6 text-brand-400" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </div>
          ) : topicAnalysis && (
            <>
              {/* AI fallback */}
              {topicAnalysis.data_source === 'ai' ? (
                <div className="bg-surface-50 rounded-xl border border-surface-200 p-6 text-center space-y-2">
                  <BookOpen size={24} className="mx-auto text-gray-600" />
                  <p className="text-sm text-gray-400">Bu ders için henüz soru verisi bulunamadı.</p>
                  <p className="text-xs text-gray-600">Analizler sekmesinden PDF yükleyin.</p>
                </div>
              ) : (
                <>
                  {/* Özet */}
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-surface-50 rounded-xl p-4 border border-surface-200 text-center">
                      <p className="text-2xl font-bold text-white">{topicAnalysis.total}</p>
                      <p className="text-xs text-gray-500 mt-0.5">Toplam Soru</p>
                    </div>
                    <div className="bg-surface-50 rounded-xl p-4 border border-surface-200 text-center">
                      <p className="text-2xl font-bold text-brand-400">{topicAnalysis.top_topics.length}</p>
                      <p className="text-xs text-gray-500 mt-0.5">Farklı Konu</p>
                    </div>
                    <div className="bg-surface-50 rounded-xl p-4 border border-surface-200 text-center">
                      <p className="text-2xl font-bold text-white">{topicAnalysis.year_breakdown.length}</p>
                      <p className="text-xs text-gray-500 mt-0.5">Yıl</p>
                    </div>
                  </div>

                  {/* Veri kaynağı badge */}
                  <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-xs">
                    <CheckCircle2 size={12} />
                    Veri kaynağı: ✓ Soru Aralıkları · ✓ Questions DB · ✓ Doğrulanmış veri
                  </div>

                  {/* Ders dağılımı (alan görünümünde) */}
                  {!selectedLesson && topicAnalysis.lesson_breakdown && topicAnalysis.lesson_breakdown.length > 1 && (
                    <div className="bg-surface-50 rounded-xl border border-surface-200 p-4">
                      <p className="text-xs font-semibold text-gray-400 mb-3">Ders Dağılımı</p>
                      <div className="space-y-2">
                        {topicAnalysis.lesson_breakdown.map(({ lesson, count }) => (
                          <div key={lesson} className="flex items-center gap-3">
                            <span className="text-xs text-gray-400 w-44 shrink-0 truncate">{lesson}</span>
                            <div className="flex-1 bg-surface-200 rounded-full h-1.5">
                              <div
                                className="bg-brand-500 h-1.5 rounded-full"
                                style={{ width: `${Math.round((count / topicAnalysis.total) * 100)}%` }}
                              />
                            </div>
                            <span className="text-xs font-mono text-gray-500 w-8 text-right">{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* En sık konular + Video + Detay */}
                  <div className="bg-surface-50 rounded-xl border border-surface-200 overflow-hidden">
                    <div className="px-5 py-3 border-b border-surface-200 flex items-center justify-between">
                      <p className="text-sm font-semibold text-gray-300">En Sık Çıkan Konular</p>
                      <span className="text-xs text-gray-500">{selectedLesson ?? selectedArea}</span>
                    </div>
                    {topicAnalysis.top_topics.length === 0 ? (
                      <div className="p-6 text-center text-sm text-gray-600">Bu alan/derse ait konu bulunamadı</div>
                    ) : (
                      <div className="divide-y divide-surface-200">
                        {topicAnalysis.top_topics.map(({ topic, count }, i) => {
                          const lesson = selectedLesson
                            ?? topicAnalysis.lesson_breakdown?.[0]?.lesson
                            ?? currentArea?.lessons[0]?.name
                            ?? ''
                          const isGenerating = generatingTopic === topic
                          const isExpanded = selectedTopic === topic
                          return (
                            <div key={topic}>
                              <div
                                className={`flex items-center gap-3 px-5 py-3 cursor-pointer transition-colors ${
                                  isExpanded ? 'bg-brand-500/5' : 'hover:bg-surface-100'
                                }`}
                                onClick={() => setSelectedTopic(isExpanded ? null : topic)}
                              >
                                <span className="text-xs font-mono text-gray-600 w-5 shrink-0">#{i + 1}</span>
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm text-gray-200 truncate">{topic}</p>
                                  <div className="flex items-center gap-2 mt-0.5">
                                    <div className="w-24 bg-surface-200 rounded-full h-1">
                                      <div
                                        className="bg-brand-500/60 h-1 rounded-full"
                                        style={{ width: `${Math.round((count / (topicAnalysis.top_topics[0]?.count || 1)) * 100)}%` }}
                                      />
                                    </div>
                                    <span className="text-xs text-gray-500">{count} soru</span>
                                  </div>
                                </div>
                                <button
                                  onClick={e => { e.stopPropagation(); if (lesson) handleGenerateVideo(lesson, topic) }}
                                  disabled={!lesson || !!generatingTopic}
                                  className="shrink-0 flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-lg bg-brand-600/10 border border-brand-500/20 text-brand-400 hover:bg-brand-600/20 disabled:opacity-40 transition-colors"
                                >
                                  {isGenerating ? (
                                    <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none">
                                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                  ) : <Video size={11} />}
                                  Video Üret
                                </button>
                                <ChevronDown
                                  size={13}
                                  className={`text-gray-600 transition-transform shrink-0 ${isExpanded ? 'rotate-180' : ''}`}
                                />
                              </div>
                              {isExpanded && (
                                <div className="px-5 pb-3 pt-2 bg-brand-500/5 border-t border-brand-500/10 space-y-2">
                                  <div className="flex items-center gap-4 flex-wrap">
                                    <div>
                                      <p className="text-[10px] text-gray-600 uppercase tracking-wide mb-0.5">Toplam</p>
                                      <p className="text-sm font-bold text-brand-300">{count} soru</p>
                                    </div>
                                    <div>
                                      <p className="text-[10px] text-gray-600 uppercase tracking-wide mb-0.5">Çıkma Oranı</p>
                                      <p className="text-sm font-bold text-gray-300">
                                        %{Math.round((count / topicAnalysis.total) * 100)}
                                      </p>
                                    </div>
                                    {lesson && (
                                      <div>
                                        <p className="text-[10px] text-gray-600 uppercase tracking-wide mb-0.5">Ders</p>
                                        <p className="text-xs text-gray-400">{lesson}</p>
                                      </div>
                                    )}
                                  </div>
                                  {topicAnalysis.year_breakdown.length > 0 && (
                                    <div>
                                      <p className="text-[10px] text-gray-600 uppercase tracking-wide mb-1">Yıllar</p>
                                      <div className="flex flex-wrap gap-1">
                                        {topicAnalysis.year_breakdown.map(({ year }) => (
                                          <span key={year} className="text-[10px] px-1.5 py-0.5 rounded bg-surface-200 text-gray-500">
                                            {year || '?'}
                                          </span>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>

                  {/* Yıl dağılımı */}
                  {topicAnalysis.year_breakdown.length > 1 && (
                    <div className="bg-surface-50 rounded-xl border border-surface-200 p-4">
                      <p className="text-xs font-semibold text-gray-400 mb-3">Yıl Dağılımı</p>
                      <div className="flex flex-wrap gap-2">
                        {topicAnalysis.year_breakdown.map(({ year, count }) => (
                          <span key={year} className="text-xs px-2.5 py-1 rounded-lg bg-surface-200 text-gray-400">
                            {year || '?'} <span className="text-gray-600">({count})</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </>
          )}
        </div>
      )}

      {!currentArea && !areasLoading && (
        <div className="flex flex-col items-center justify-center py-12 text-center text-gray-600">
          <BarChart2 size={36} className="mb-3 text-gray-700" />
          <p className="text-sm">Bir alan kartına tıklayarak ders dağılımını ve konu analizini gör</p>
          <p className="text-xs mt-1">Soru aralıkları tanımlandıkça kartlar otomatik güncellenir</p>
        </div>
      )}


      {/* Soru Aralıkları — sadece gelişmiş modda */}
      <details className="border-t border-surface-200 pt-4">
        <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-400 select-none mb-4">
          Gelişmiş: Soru Aralıkları Yönetimi
        </summary>
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <List size={14} className="text-gray-500" />
            <span className="text-sm font-semibold text-gray-300">
              Soru Aralıkları {!rangesLoading && `(${ranges.length})`}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Button size="sm" variant="secondary" onClick={() => { setShowBulkModal(true); setShowRangeForm(false) }}>
              <Layers size={13} /> Toplu Oluştur
            </Button>
            <Button size="sm" variant="secondary" onClick={() => { setShowRangeForm(f => !f); setShowBulkModal(false) }}>
              <Plus size={13} /> {showRangeForm ? 'Kapat' : 'Yeni Aralık'}
            </Button>
          </div>
        </div>

        {/* Alan bazlı silme */}
        {ranges.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {Object.keys(SGS_LESSON_GROUPS).map(area => {
              const areaLessons = SGS_LESSON_GROUPS[area as keyof typeof SGS_LESSON_GROUPS] ?? []
              const count = ranges.filter(r => (areaLessons as readonly string[]).includes(r.lesson_name)).length
              if (count === 0) return null
              return (
                <button
                  key={area}
                  onClick={() => handleDeleteByArea(area)}
                  className="flex items-center gap-1 text-[11px] px-2.5 py-1 rounded-lg bg-surface-100 border border-surface-200 text-gray-500 hover:text-red-400 hover:border-red-500/30 transition-colors"
                  title={`${area} aralıklarını sil`}
                >
                  <Trash2 size={10} /> {area} ({count})
                </button>
              )
            })}
          </div>
        )}

        {/* Yeni aralık formu */}
        {showRangeForm && (
          <div className="bg-surface-50 rounded-xl border border-surface-200 p-5 mb-4">
            <form onSubmit={handleSaveRange} className="space-y-4" noValidate>
              <div>
                <label className="text-xs font-medium text-gray-400 mb-1 block">PDF Seç</label>
                {pdfOptions.length === 0 ? (
                  <p className="text-xs text-yellow-400 py-2">
                    Henüz yüklü PDF analizi yok. Önce &quot;Analizler&quot; sekmesinden PDF yükleyin.
                  </p>
                ) : (
                  <select
                    className="w-full bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    value={rangeForm.document_id}
                    onChange={e => {
                      const picked = pdfOptions.find(a => a.id === e.target.value)
                      setRangeForm(f => ({
                        ...f,
                        document_id: e.target.value,
                        document_name: picked?.pdf_name ?? '',
                      }))
                    }}
                  >
                    <option value="">— PDF seçin —</option>
                    {pdfOptions.map(a => (
                      <option key={a.id} value={a.id}>
                        {a.pdf_name}{a.year ? ` (${a.year}${a.semester ? ' · ' + a.semester : ''})` : ''}
                      </option>
                    ))}
                  </select>
                )}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-400 mb-1 block">Başlangıç Sorusu</label>
                  <input
                    type="number" min={1}
                    className="w-full bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    placeholder="1"
                    value={rangeForm.start_question_no}
                    onChange={e => setRangeForm(f => ({ ...f, start_question_no: e.target.value }))}
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-400 mb-1 block">Bitiş Sorusu</label>
                  <input
                    type="number" min={1}
                    className="w-full bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    placeholder="20"
                    value={rangeForm.end_question_no}
                    onChange={e => setRangeForm(f => ({ ...f, end_question_no: e.target.value }))}
                  />
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-400 mb-1 block">Ders</label>
                <select
                  className="w-full bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  value={rangeForm.lesson_name}
                  onChange={e => setRangeForm(f => ({ ...f, lesson_name: e.target.value }))}
                >
                  {Object.entries(SGS_LESSON_GROUPS).map(([group, lessons]) => (
                    <optgroup key={group} label={group}>
                      {lessons.map(l => <option key={l} value={l}>{l}</option>)}
                    </optgroup>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-400 mb-1 block">Not (isteğe bağlı)</label>
                <input
                  className="w-full bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500 placeholder-gray-600"
                  placeholder="örn: İlk 20 soru Türkçe bölümüne ait"
                  value={rangeForm.notes}
                  onChange={e => setRangeForm(f => ({ ...f, notes: e.target.value }))}
                />
              </div>
              <Button type="submit" isLoading={savingRange} disabled={savingRange}>
                <Plus size={14} /> Kaydet
              </Button>
            </form>
          </div>
        )}

        {/* Aralık listesi */}
        <div className="bg-surface-50 rounded-xl border border-surface-200 overflow-hidden">
          {rangesLoading ? (
            <div className="p-6 text-center text-gray-600 text-sm">Yükleniyor...</div>
          ) : ranges.length === 0 ? (
            <div className="p-6 text-center text-gray-600 text-sm">
              Henüz aralık tanımlanmadı. &quot;Yeni Aralık&quot; butonuyla başla.
            </div>
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
                      <span className="text-xs text-gray-600">({r.end_question_no - r.start_question_no + 1} soru)</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5 truncate">
                      {r.document_name}{r.notes ? ` · ${r.notes}` : ''}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDeleteRange(r.id)}
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
      </details>

      {/* Toplu Aralık Oluşturma Modalı */}
      {showBulkModal && (
        <BulkRangeModal
          pdfOptions={pdfOptions}
          existingRanges={ranges}
          onClose={() => setShowBulkModal(false)}
          onSaved={async () => {
            setShowBulkModal(false)
            const updated = await sgsService.listRanges()
            setRanges(updated)
            loadAreas(yearFilter || undefined)
          }}
        />
      )}
    </div>
  )
}

const GROUP_COLORS: Record<string, string> = {
  'Genel Dersler': 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  'Hukuk': 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  'Muhasebe': 'text-green-400 bg-green-500/10 border-green-500/20',
  'Finans': 'text-orange-400 bg-orange-500/10 border-orange-500/20',
}

function CategorySummary({ questions }: { questions: SgsAnalysis['questions'] }) {
  const [openGroup, setOpenGroup] = useState<string | null>(null)

  const groupStats = Object.entries(SGS_LESSON_GROUPS).map(([group, lessons]) => {
    const groupQuestions = questions.filter(q => (lessons as readonly string[]).includes(q.subject))
    const lessonBreakdown = lessons.map(lesson => ({
      lesson,
      count: questions.filter(q => q.subject === lesson).length,
    })).filter(l => l.count > 0)
    return { group, count: groupQuestions.length, lessons: lessonBreakdown }
  }).filter(g => g.count > 0)

  if (groupStats.length === 0) return null

  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Alan Dağılımı</p>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {groupStats.map(({ group, count, lessons }) => {
          const colorClass = GROUP_COLORS[group] ?? 'text-gray-400 bg-surface-100 border-surface-200'
          const isOpen = openGroup === group
          return (
            <div key={group} className={`rounded-xl border overflow-hidden ${colorClass.split(' ').slice(1).join(' ')}`}>
              <button
                onClick={() => setOpenGroup(isOpen ? null : group)}
                className="w-full p-3 text-left"
              >
                <p className={`text-lg font-bold ${colorClass.split(' ')[0]}`}>{count}</p>
                <p className="text-xs text-gray-400 mt-0.5">{group}</p>
                <p className="text-[10px] text-gray-600 mt-0.5">{lessons.length} ders</p>
              </button>
              {isOpen && (
                <div className="border-t border-white/5 px-3 pb-3 space-y-1">
                  {lessons.map(({ lesson, count: lCount }) => (
                    <div key={lesson} className="flex items-center justify-between">
                      <span className="text-xs text-gray-400 truncate">{lesson}</span>
                      <span className="text-xs font-mono text-gray-500 ml-2 shrink-0">({lCount})</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
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
  const [groupFilter, setGroupFilter] = useState<string | null>(null)

  const subjects = Array.from(new Set(analysis.questions.map(q => q.subject)))
  const uncertainCount = analysis.questions.filter(q =>
    q.subject === 'Belirsiz' || (q.lesson_confidence !== undefined && q.lesson_confidence < 0.6)
  ).length

  const filteredQ = analysis.questions.filter(q => {
    if (subjFilter === 'Belirsiz') return q.subject === 'Belirsiz' || (q.lesson_confidence !== undefined && q.lesson_confidence < 0.6)
    if (subjFilter !== 'Tümü') return q.subject === subjFilter
    if (groupFilter) {
      const groupLessons = SGS_LESSON_GROUPS[groupFilter as keyof typeof SGS_LESSON_GROUPS]
      return groupLessons ? (groupLessons as readonly string[]).includes(q.subject) : true
    }
    return true
  })

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

      <CategorySummary questions={analysis.questions} />

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
          {/* Grup filtresi */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => { setGroupFilter(null); setSubjFilter('Tümü') }}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                !groupFilter && subjFilter === 'Tümü'
                  ? 'bg-brand-600/20 border-brand-500/50 text-brand-300'
                  : 'bg-surface-100 border-surface-200 text-gray-500 hover:text-gray-300'
              }`}
            >
              Tümü ({analysis.total_questions})
            </button>
            {uncertainCount > 0 && (
              <button
                onClick={() => { setGroupFilter(null); setSubjFilter('Belirsiz') }}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                  subjFilter === 'Belirsiz'
                    ? 'bg-yellow-500/20 border-yellow-500/40 text-yellow-300'
                    : 'bg-surface-100 border-surface-200 text-gray-500 hover:text-gray-300'
                }`}
              >
                Belirsiz ({uncertainCount})
              </button>
            )}
            {Object.entries(SGS_LESSON_GROUPS).map(([group, lessons]) => {
              const count = analysis.questions.filter(q => (lessons as readonly string[]).includes(q.subject)).length
              if (count === 0) return null
              const colorClass = GROUP_COLORS[group] ?? 'text-gray-400 bg-surface-100 border-surface-200'
              const isActive = groupFilter === group && subjFilter === 'Tümü'
              return (
                <button
                  key={group}
                  onClick={() => { setGroupFilter(group); setSubjFilter('Tümü') }}
                  className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                    isActive
                      ? colorClass
                      : 'bg-surface-100 border-surface-200 text-gray-500 hover:text-gray-300'
                  }`}
                >
                  {group} ({count})
                </button>
              )
            })}
          </div>

          {/* Ders filtresi (grup seçiliyken) */}
          {groupFilter && (
            <div className="flex flex-wrap gap-1.5 pl-2 border-l-2 border-surface-300">
              {(SGS_LESSON_GROUPS[groupFilter as keyof typeof SGS_LESSON_GROUPS] as readonly string[])
                .filter(lesson => subjects.includes(lesson))
                .map(lesson => {
                  const count = analysis.questions.filter(q => q.subject === lesson).length
                  return (
                    <button
                      key={lesson}
                      onClick={() => setSubjFilter(subjFilter === lesson ? 'Tümü' : lesson)}
                      className={`text-xs px-2.5 py-1 rounded-lg border transition-colors ${
                        subjFilter === lesson
                          ? 'bg-brand-600/20 border-brand-500/50 text-brand-300'
                          : 'bg-surface-50 border-surface-200 text-gray-500 hover:text-gray-300'
                      }`}
                    >
                      {lesson} ({count})
                    </button>
                  )
                })}
            </div>
          )}

          <div className="space-y-2">
            {filteredQ.length === 0 ? (
              <p className="text-sm text-gray-600 text-center py-6">Bu filtrede soru yok</p>
            ) : (
              filteredQ.map(q => (
                <QuestionRow
                  key={q.id}
                  question={q}
                  analysisId={analysis.analysis_id}
                  onLessonChange={onLessonChange}
                />
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default function AcademyPage() {
  const [pageTab, setPageTab] = useState<'analyses' | 'area-analysis'>('analyses')
  const [phase, setPhase] = useState<Phase>('idle')
  const [areaReloadKey, setAreaReloadKey] = useState(0)
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

      // Analiz biter bitmez soruları otomatik kaydet
      if (result.analysis_id) {
        try {
          const parseResult = await sgsService.parseQuestions({ analysis_id: result.analysis_id })
          if (parseResult.questions_created > 0) {
            toast.success(`${parseResult.questions_created} soru veritabanına kaydedildi`)
            setAreaReloadKey(k => k + 1)
          }
        } catch {
          // Aralık yoksa sessizce geç — kullanıcı daha sonra bağlayabilir
        }
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string }
      const detail = axiosErr?.response?.data?.detail
      const msg = detail ?? axiosErr?.message ?? 'Analiz başarısız'
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
              onClick={() => setPageTab('area-analysis')}
              className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                pageTab === 'area-analysis' ? 'bg-surface-50 text-white shadow-sm' : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              <BarChart2 size={13} /> Alan Analizi
            </button>
          </div>
        </div>

        {pageTab === 'area-analysis' && <AreaAnalysisPanel key={areaReloadKey} />}

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
          <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl space-y-3">
            <div className="flex items-start gap-2">
              <AlertTriangle size={16} className="text-red-400 mt-0.5 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-red-300">Analiz Hatası</p>
                <p className="text-xs text-red-400/80 mt-0.5 break-words">{error}</p>
              </div>
            </div>
            <div className="flex gap-2">
              <label
                htmlFor="sgs-pdf-input"
                className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-red-500/20 border border-red-500/30 text-red-300 cursor-pointer hover:bg-red-500/30 transition-colors"
              >
                <RefreshCw size={12} /> Yeniden Dene
              </label>
              <button
                onClick={() => setError(null)}
                className="text-xs px-3 py-1.5 rounded-lg bg-surface-100 border border-surface-200 text-gray-500 hover:text-gray-300 transition-colors"
              >
                Kapat
              </button>
            </div>
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
