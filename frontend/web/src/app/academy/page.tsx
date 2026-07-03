'use client'

import { useCallback, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import AppShell from '@/components/layout/AppShell'
import Button from '@/components/ui/Button'
import {
  GraduationCap, Upload, FileText, Video, Trash2, RefreshCw,
  BarChart2, BookOpen, ChevronDown, Clock,
} from 'lucide-react'
import {
  sgsService, SGS_DOCUMENT_TYPES, SGS_LESSONS, TOPIC_LESSON_MAP,
  type SgsArea, type SgsTopicAnalysis, type SgsAnalysisMeta, type SgsTopicDetail, type SgsQuestion,
} from '@/services/sgs.service'
import toast from 'react-hot-toast'

type PageTab = 'dashboard' | 'upload'

const AREA_CFG: Record<string, {
  color: string; barColor: string; bg: string; border: string
}> = {
  'Genel Dersler': { color: 'text-blue-400', barColor: 'bg-blue-500', bg: 'bg-blue-500/08', border: 'border-blue-500/35' },
  'Hukuk':         { color: 'text-purple-400', barColor: 'bg-purple-500', bg: 'bg-purple-500/08', border: 'border-purple-500/35' },
  'Muhasebe':      { color: 'text-emerald-400', barColor: 'bg-emerald-500', bg: 'bg-emerald-500/08', border: 'border-emerald-500/35' },
  'Finans':        { color: 'text-orange-400', barColor: 'bg-orange-500', bg: 'bg-orange-500/08', border: 'border-orange-500/35' },
}
const DEFAULT_CFG = { color: 'text-gray-400', barColor: 'bg-surface-300', bg: 'bg-surface-100', border: 'border-surface-200' }

function Spinner({ size = 5 }: { size?: number }) {
  return (
    <svg className={`animate-spin h-${size} w-${size} text-brand-400`} viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}

// ── Question Card ─────────────────────────────────────────────
const OPTION_LABELS = ['A', 'B', 'C', 'D', 'E']

function QuestionCard({ question, onMoved }: {
  question: SgsQuestion
  onMoved?: () => void
}) {
  const [open, setOpen] = useState(false)
  const [editLesson, setEditLesson] = useState(false)
  const [selectedLesson, setSelectedLesson] = useState(
    () => TOPIC_LESSON_MAP[question.topic] ?? question.subject
  )
  const [saving, setSaving] = useState(false)

  const suggestedLesson = TOPIC_LESSON_MAP[question.topic]
  const isWrongLesson = suggestedLesson && suggestedLesson !== question.subject

  const handleLessonSave = async () => {
    if (selectedLesson === question.subject) { setEditLesson(false); return }
    setSaving(true)
    try {
      await sgsService.updateQuestionById(question.id, { lesson_name: selectedLesson })
      toast.success(`Ders "${selectedLesson}" olarak güncellendi`)
      onMoved?.()
    } catch {
      toast.error('Ders güncellenemedi')
    } finally {
      setSaving(false)
      setEditLesson(false)
    }
  }

  return (
    <div className="border border-surface-200 rounded-xl bg-surface-50/30 overflow-hidden">
      <div
        className="flex items-center gap-2 px-3 py-2.5 cursor-pointer hover:bg-surface-100/30 transition-colors"
        onClick={() => setOpen(!open)}
      >
        <span className="text-[10px] font-mono text-gray-600 shrink-0">#{question.id}</span>
        {question.year && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface-200 text-gray-500 shrink-0">{question.year}</span>
        )}
        {isWrongLesson && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-orange-500/10 border border-orange-500/20 text-orange-400 shrink-0">
            {question.subject}
          </span>
        )}
        <p className="text-xs text-gray-400 truncate flex-1">
          {question.question_text?.slice(0, 90)}{(question.question_text?.length ?? 0) > 90 ? '…' : ''}
        </p>
        <ChevronDown size={11} className={`text-gray-600 transition-transform shrink-0 ${open ? 'rotate-180' : ''}`} />
      </div>

      {open && (
        <div className="border-t border-surface-200/40 px-3 pb-3 pt-2.5 space-y-3">
          <p className="text-sm text-gray-200 leading-relaxed">{question.question_text}</p>

          {question.options.length > 0 && (
            <div className="space-y-1.5">
              {question.options.map((opt, i) => {
                const label = OPTION_LABELS[i]
                const isCorrect = label === question.correct_option
                return (
                  <div
                    key={i}
                    className={`flex items-start gap-2 rounded-lg px-2.5 py-2 text-xs ${
                      isCorrect
                        ? 'bg-emerald-500/10 border border-emerald-500/25 text-emerald-300'
                        : 'bg-surface-100/40 text-gray-400'
                    }`}
                  >
                    <span className={`font-bold shrink-0 w-4 ${isCorrect ? 'text-emerald-400' : 'text-gray-600'}`}>{label}</span>
                    <span className="leading-relaxed flex-1">{opt}</span>
                    {isCorrect && <span className="shrink-0 text-emerald-400 text-[10px] font-bold ml-auto">DOĞRU</span>}
                  </div>
                )
              })}
            </div>
          )}

          {question.explanation && (
            <div className="bg-brand-500/06 border-l-2 border-brand-500/40 pl-3 py-1.5 rounded-r-lg">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-brand-400 mb-0.5">Açıklama</p>
              <p className="text-xs text-gray-400 leading-relaxed">{question.explanation}</p>
            </div>
          )}

          <div className="flex items-center justify-between flex-wrap gap-2 pt-0.5">
            <div className="flex flex-wrap gap-1.5">
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-surface-200 text-gray-500">{question.subject}</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-surface-200 text-gray-500">{question.topic}</span>
              {question.document_name && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-surface-200 text-gray-500 truncate max-w-[180px]">
                  {question.document_name}
                </span>
              )}
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); setEditLesson(!editLesson) }}
              className="text-[10px] px-2.5 py-1 rounded-lg border border-surface-200 text-gray-500 hover:text-gray-300 hover:border-surface-300 transition-colors"
            >
              Dersi Değiştir
            </button>
          </div>

          {editLesson && (
            <div className="flex items-center gap-2 pt-0.5" onClick={e => e.stopPropagation()}>
              <select
                className="flex-1 bg-surface-100 border border-surface-200 rounded-lg px-2 py-1.5 text-xs text-gray-100 focus:outline-none focus:ring-1 focus:ring-brand-500"
                value={selectedLesson}
                onChange={e => setSelectedLesson(e.target.value)}
              >
                {SGS_LESSONS.map(l => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
              <button
                onClick={handleLessonSave}
                disabled={saving || selectedLesson === question.subject}
                className="text-xs px-2.5 py-1.5 rounded-lg bg-brand-600/20 border border-brand-500/30 text-brand-400 hover:bg-brand-600/30 disabled:opacity-40 transition-colors shrink-0"
              >
                {saving ? '…' : 'Kaydet'}
              </button>
              <button
                onClick={() => setEditLesson(false)}
                className="text-xs text-gray-600 hover:text-gray-300 shrink-0 transition-colors"
              >
                İptal
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Topic Row ─────────────────────────────────────────────────
function TopicRow({ topic, count, maxCount, lessonName, rank, generatingTopic, onGenerate }: {
  topic: string
  count: number
  maxCount: number
  lessonName: string
  rank: number
  generatingTopic: string | null
  onGenerate: (lesson: string, topic: string) => void
}) {
  const [open, setOpen] = useState(false)
  const [detail, setDetail] = useState<SgsTopicDetail | null>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [questions, setQuestions] = useState<SgsQuestion[]>([])
  const [loadingQuestions, setLoadingQuestions] = useState(false)
  const [questionsLoaded, setQuestionsLoaded] = useState(false)
  const barPct = Math.round((count / (maxCount || 1)) * 100)
  const isGen = generatingTopic === topic

  const handleExpand = () => {
    const next = !open
    setOpen(next)
    if (next && !detail && !loadingDetail) {
      setLoadingDetail(true)
      sgsService.getTopicDetail(topic, lessonName)
        .then(d => setDetail(d))
        .catch(() => {})
        .finally(() => setLoadingDetail(false))
    }
    if (next && !questionsLoaded && !loadingQuestions) {
      setLoadingQuestions(true)
      sgsService.getTopicQuestions(topic, lessonName)
        .then(qs => { setQuestions(qs); setQuestionsLoaded(true) })
        .catch(() => { setQuestionsLoaded(true) })
        .finally(() => setLoadingQuestions(false))
    }
  }

  const handleQuestionMoved = (id: number) => {
    setQuestions(prev => prev.filter(q => q.id !== id))
  }

  return (
    <div className="border-b border-surface-200 last:border-0">
      <div
        className="flex items-center gap-3 px-5 py-3 cursor-pointer hover:bg-surface-100/30 transition-colors"
        onClick={handleExpand}
      >
        <span className="text-[11px] font-mono text-gray-600 w-5 shrink-0">#{rank}</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-200 truncate mb-1.5">{topic}</p>
          <div className="flex items-center gap-2">
            <div className="flex-1 max-w-[200px] bg-surface-200 rounded-full h-1.5">
              <div className="bg-brand-500 h-1.5 rounded-full" style={{ width: `${barPct}%` }} />
            </div>
            <span className="text-xs text-gray-500 shrink-0">{count} soru</span>
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0" onClick={e => e.stopPropagation()}>
          <button
            onClick={() => onGenerate(lessonName, topic)}
            disabled={!!generatingTopic}
            className="flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-lg bg-brand-600/10 border border-brand-500/20 text-brand-400 hover:bg-brand-600/20 disabled:opacity-40 transition-colors"
          >
            {isGen ? <Spinner size={3} /> : <Video size={11} />}
            Video Üret
          </button>
        </div>
        <ChevronDown size={13} className={`text-gray-600 transition-transform shrink-0 ${open ? 'rotate-180' : ''}`} />
      </div>

      {open && (
        <div className="px-5 pb-4 pt-2 bg-surface-100/20 border-t border-surface-200/50 space-y-3">
          {/* Topic meta */}
          {loadingDetail ? (
            <div className="flex items-center gap-2 py-1"><Spinner size={4} /><span className="text-xs text-gray-500">Yükleniyor...</span></div>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center gap-5 flex-wrap">
                <div>
                  <p className="text-[10px] text-gray-600 uppercase tracking-wide mb-0.5">Toplam</p>
                  <p className="text-sm font-bold text-brand-300">{detail?.total_questions ?? count} soru</p>
                </div>
                {detail && (
                  <div>
                    <p className="text-[10px] text-gray-600 uppercase tracking-wide mb-0.5">Çıkma Oranı</p>
                    <p className="text-sm font-bold text-gray-300">%{Math.round(detail.frequency_pct)}</p>
                  </div>
                )}
              </div>
              {detail && detail.years.length > 0 && (
                <div>
                  <p className="text-[10px] text-gray-600 uppercase tracking-wide mb-1.5">Çıktığı Yıllar</p>
                  <div className="flex flex-wrap gap-1">
                    {detail.years.map(({ year, count: yc }) => (
                      <span key={year} className="text-[11px] px-2 py-0.5 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-300">
                        {year} <span className="opacity-60">({yc})</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Questions */}
          <div className="pt-3 border-t border-surface-200/40">
            <p className="text-[10px] uppercase tracking-wide text-gray-600 font-semibold mb-2">
              Sorular {questions.length > 0 && <span className="text-gray-700">({questions.length})</span>}
            </p>
            {loadingQuestions ? (
              <div className="flex items-center gap-2">
                <Spinner size={3} />
                <span className="text-xs text-gray-500">Sorular yükleniyor...</span>
              </div>
            ) : questionsLoaded && questions.length === 0 ? (
              <p className="text-xs text-gray-600">Bu konuya ait soru bulunamadı.</p>
            ) : (
              <div className="space-y-2">
                {questions.map(q => (
                  <QuestionCard
                    key={q.id}
                    question={q}
                    onMoved={() => handleQuestionMoved(q.id)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Topic Dashboard ────────────────────────────────────────────
function TopicDashboard({ lessonName, yearFilter, generatingTopic, onGenerate }: {
  lessonName: string
  yearFilter: string
  generatingTopic: string | null
  onGenerate: (lesson: string, topic: string) => void
}) {
  const [data, setData] = useState<SgsTopicAnalysis | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setData(null)
    sgsService.getLessonTopicAnalysis(lessonName, yearFilter || undefined)
      .then(d => { if (!cancelled) setData(d) })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [lessonName, yearFilter])

  if (loading) return <div className="flex justify-center py-8"><Spinner size={6} /></div>

  if (!data || data.total === 0) {
    return (
      <div className="text-center py-8">
        <BookOpen size={24} className="mx-auto text-gray-700 mb-2" />
        <p className="text-sm text-gray-500">Bu ders için henüz soru kaydedilmedi.</p>
        <p className="text-xs text-gray-600 mt-0.5">PDF sekmesinden ilgili sınav dosyasını yükleyin.</p>
      </div>
    )
  }

  const topTopic = data.top_topics[0]
  const topPct = topTopic ? Math.round((topTopic.count / data.total) * 100) : 0

  return (
    <div className="space-y-4 pt-2">
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-surface-50 rounded-xl border border-surface-200 p-3 text-center">
          <p className="text-xl font-bold text-white">{data.total}</p>
          <p className="text-[11px] text-gray-500 mt-0.5">Toplam Soru</p>
        </div>
        <div className="bg-surface-50 rounded-xl border border-surface-200 p-3 text-center">
          <p className="text-xl font-bold text-brand-400">{data.top_topics.length}</p>
          <p className="text-[11px] text-gray-500 mt-0.5">Konu</p>
        </div>
        <div className="bg-surface-50 rounded-xl border border-surface-200 p-3 text-center">
          <p className="text-xl font-bold text-white">{data.year_breakdown.length}</p>
          <p className="text-[11px] text-gray-500 mt-0.5">Yıl</p>
        </div>
      </div>

      {topTopic && (
        <div className="bg-brand-500/08 border border-brand-500/20 rounded-xl px-4 py-3 flex items-center justify-between">
          <div>
            <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-0.5">En Çok Çıkan</p>
            <p className="text-sm font-semibold text-brand-300">{topTopic.topic}</p>
          </div>
          <div className="text-right">
            <p className="text-xl font-bold text-brand-400">%{topPct}</p>
            <p className="text-[11px] text-gray-600">{topTopic.count} soru</p>
          </div>
        </div>
      )}

      {data.year_breakdown.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {data.year_breakdown.map(({ year, count }) => (
            <span key={year} className="text-xs px-2.5 py-1 rounded-lg bg-surface-200 text-gray-400">
              {year || '?'} <span className="text-gray-600">({count})</span>
            </span>
          ))}
        </div>
      )}

      <div className="bg-surface-50 rounded-xl border border-surface-200 overflow-hidden">
        <div className="px-5 py-3 border-b border-surface-200">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Konu Dağılımı</p>
        </div>
        {data.top_topics.map(({ topic, count }, i) => (
          <TopicRow
            key={topic}
            topic={topic}
            count={count}
            maxCount={data.top_topics[0]?.count ?? 1}
            lessonName={lessonName}
            rank={i + 1}
            generatingTopic={generatingTopic}
            onGenerate={onGenerate}
          />
        ))}
      </div>
    </div>
  )
}

// ── Lesson Panel ───────────────────────────────────────────────
function LessonPanel({ area, yearFilter, generatingTopic, onGenerate, onAreaAnalyze }: {
  area: SgsArea
  yearFilter: string
  generatingTopic: string | null
  onGenerate: (lesson: string, topic: string) => void
  onAreaAnalyze: () => void
}) {
  const [selectedLesson, setSelectedLesson] = useState<string | null>(null)
  const cfg = AREA_CFG[area.name] ?? DEFAULT_CFG

  return (
    <div className="bg-surface-50 rounded-2xl border border-surface-200 overflow-hidden">
      <div className="px-5 py-3.5 border-b border-surface-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`text-sm font-bold ${cfg.color}`}>{area.name}</span>
          <span className="text-xs text-gray-600">{area.found_total} soru · {area.lessons.length} ders</span>
        </div>
        <Button size="sm" variant="ghost" onClick={onAreaAnalyze}>
          <BarChart2 size={12} /> Tüm Alan
        </Button>
      </div>

      <div className="divide-y divide-surface-200">
        {area.lessons.map(lesson => {
          const isOpen = selectedLesson === lesson.name
          return (
            <div key={lesson.name}>
              <div
                className={`flex items-center justify-between px-5 py-3.5 cursor-pointer transition-colors ${
                  isOpen ? cfg.bg : 'hover:bg-surface-100/30'
                }`}
                onClick={() => setSelectedLesson(isOpen ? null : lesson.name)}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <p className={`text-sm font-medium truncate ${isOpen ? cfg.color : 'text-gray-300'}`}>
                    {lesson.name}
                  </p>
                  {lesson.found > 0 && (
                    <span className="text-[11px] text-emerald-400 shrink-0 font-medium">
                      {lesson.found} soru
                    </span>
                  )}
                </div>
                <ChevronDown size={13} className={`text-gray-600 transition-transform shrink-0 ${isOpen ? 'rotate-180' : ''}`} />
              </div>

              {isOpen && (
                <div className="px-5 pb-5 bg-surface-100/20 border-t border-surface-200/50">
                  <TopicDashboard
                    lessonName={lesson.name}
                    yearFilter={yearFilter}
                    generatingTopic={generatingTopic}
                    onGenerate={onGenerate}
                  />
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Area-level Analysis Panel ─────────────────────────────────
function AreaAnalysisPanel({ areaName, data, onBack, generatingTopic, onGenerate }: {
  areaName: string
  data: SgsTopicAnalysis
  onBack: () => void
  generatingTopic: string | null
  onGenerate: (lesson: string, topic: string) => void
}) {
  const firstLesson = data.lesson_breakdown?.[0]?.lesson ?? ''

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-gray-300">{areaName} — Genel Analiz</p>
        <button onClick={onBack} className="text-xs text-gray-500 hover:text-gray-300 transition-colors">
          ← Derslere Dön
        </button>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="bg-surface-50 rounded-xl border border-surface-200 p-3 text-center">
          <p className="text-xl font-bold text-white">{data.total}</p>
          <p className="text-[11px] text-gray-500 mt-0.5">Toplam Soru</p>
        </div>
        <div className="bg-surface-50 rounded-xl border border-surface-200 p-3 text-center">
          <p className="text-xl font-bold text-brand-400">{data.top_topics.length}</p>
          <p className="text-[11px] text-gray-500 mt-0.5">Konu</p>
        </div>
        <div className="bg-surface-50 rounded-xl border border-surface-200 p-3 text-center">
          <p className="text-xl font-bold text-white">{data.year_breakdown.length}</p>
          <p className="text-[11px] text-gray-500 mt-0.5">Yıl</p>
        </div>
      </div>

      {data.lesson_breakdown && data.lesson_breakdown.length > 1 && (
        <div className="bg-surface-50 rounded-xl border border-surface-200 p-4">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Ders Dağılımı</p>
          <div className="space-y-2">
            {data.lesson_breakdown.map(({ lesson, count }) => (
              <div key={lesson} className="flex items-center gap-3">
                <span className="text-xs text-gray-400 w-44 shrink-0 truncate">{lesson}</span>
                <div className="flex-1 bg-surface-200 rounded-full h-1.5">
                  <div
                    className="bg-brand-500 h-1.5 rounded-full"
                    style={{ width: `${Math.round((count / data.total) * 100)}%` }}
                  />
                </div>
                <span className="text-xs font-mono text-gray-500 w-8 text-right">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.top_topics.length > 0 && (
        <div className="bg-surface-50 rounded-xl border border-surface-200 overflow-hidden">
          <div className="px-5 py-3 border-b border-surface-200">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">En Çok Çıkan Konular</p>
          </div>
          {data.top_topics.map(({ topic, count }, i) => (
            <TopicRow
              key={topic}
              topic={topic}
              count={count}
              maxCount={data.top_topics[0]?.count ?? 1}
              lessonName={firstLesson}
              rank={i + 1}
              generatingTopic={generatingTopic}
              onGenerate={onGenerate}
            />
          ))}
        </div>
      )}

      {data.year_breakdown.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {data.year_breakdown.map(({ year, count }) => (
            <span key={year} className="text-xs px-2.5 py-1 rounded-lg bg-surface-200 text-gray-400">
              {year || '?'} <span className="text-gray-600">({count})</span>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Dashboard Tab ─────────────────────────────────────────────
function DashboardTab({ reloadKey }: { reloadKey: number }) {
  const router = useRouter()
  const [areas, setAreas] = useState<SgsArea[]>([])
  const [loading, setLoading] = useState(true)
  const [yearFilter, setYearFilter] = useState('')
  const [selectedArea, setSelectedArea] = useState<string | null>(null)
  const [generatingTopic, setGeneratingTopic] = useState<string | null>(null)
  const [areaAnalysis, setAreaAnalysis] = useState<SgsTopicAnalysis | null>(null)
  const [areaAnalysisLoading, setAreaAnalysisLoading] = useState(false)
  const [showAreaAnalysis, setShowAreaAnalysis] = useState(false)
  const [reclassifying, setReclassifying] = useState(false)
  const [parsingAll, setParsingAll] = useState(false)

  const loadAreas = useCallback(async (year?: string) => {
    setLoading(true)
    try { setAreas(await sgsService.getAreas(year || undefined)) }
    catch { toast.error('Alan verileri yüklenemedi') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { loadAreas() }, [loadAreas, reloadKey])

  const handleAreaClick = (name: string) => {
    if (selectedArea === name) {
      setSelectedArea(null); setAreaAnalysis(null); setShowAreaAnalysis(false)
    } else {
      setSelectedArea(name); setAreaAnalysis(null); setShowAreaAnalysis(false)
    }
  }

  const handleAreaAnalyze = async () => {
    if (!selectedArea) return
    setAreaAnalysisLoading(true)
    setShowAreaAnalysis(true)
    setAreaAnalysis(null)
    try {
      setAreaAnalysis(await sgsService.getAreaTopicAnalysis(selectedArea, yearFilter || undefined))
    } catch { toast.error('Alan analizi yapılamadı') }
    finally { setAreaAnalysisLoading(false) }
  }

  const handleParseAll = async () => {
    setParsingAll(true)
    try {
      const result = await sgsService.parseAllAnalyses()
      if (result.total_created === 0) {
        toast.success('Tüm analizler zaten parse edilmiş')
      } else {
        toast.success(`${result.total_created} soru parse edildi`)
        loadAreas(yearFilter || undefined)
      }
    } catch {
      toast.error('Parse işlemi başarısız')
    } finally {
      setParsingAll(false)
    }
  }

  const handleReclassify = async () => {
    setReclassifying(true)
    try {
      const result = await sgsService.reclassifyQuestions()
      if (result.updated === 0) {
        toast.success('Tüm sorular zaten doğru sınıflandırılmış')
      } else {
        toast.success(`${result.updated} soru yeniden sınıflandırıldı`)
        loadAreas(yearFilter || undefined)
      }
    } catch {
      toast.error('Yeniden sınıflandırma başarısız')
    } finally {
      setReclassifying(false)
    }
  }

  const handleGenerate = async (lesson: string, topic: string) => {
    setGeneratingTopic(topic)
    try {
      await sgsService.generateTopicVideo({ lesson, topic, year: yearFilter || undefined, max_questions: 5 })
      toast.success(`"${topic}" video üretimi başlatıldı`)
      router.push('/video')
    } catch { toast.error('Video üretimi başlatılamadı') }
    finally { setGeneratingTopic(null) }
  }

  const currentArea = areas.find(a => a.name === selectedArea)

  return (
    <div className="space-y-6">
      {/* Filter bar */}
      <div className="flex items-center gap-3">
        <input
          type="text"
          placeholder="Yıl filtresi (örn: 2024)"
          value={yearFilter}
          onChange={e => { setYearFilter(e.target.value); setAreaAnalysis(null); setShowAreaAnalysis(false) }}
          className="max-w-[200px] bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500 placeholder-gray-600"
        />
        <Button size="sm" variant="ghost" onClick={() => loadAreas(yearFilter || undefined)} isLoading={loading}>
          <RefreshCw size={13} /> Yenile
        </Button>
        <Button size="sm" variant="ghost" onClick={handleParseAll} isLoading={parsingAll}>
          <RefreshCw size={13} /> Tümünü Parse Et
        </Button>
        <Button size="sm" variant="ghost" onClick={handleReclassify} isLoading={reclassifying}>
          <RefreshCw size={13} /> Yeniden Sınıflandır
        </Button>
      </div>

      {/* Area cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-32 bg-surface-100 rounded-2xl border border-surface-200 animate-pulse" />
          ))
        ) : areas.map(area => {
          const cfg = AREA_CFG[area.name] ?? DEFAULT_CFG
          const isActive = selectedArea === area.name
          const successRate = area.found_total > 0 && area.expected_total > 0
            ? Math.min(100, Math.round((area.found_total / area.expected_total) * 100))
            : area.found_total > 0 ? 100 : 0
          const lessonsWithData = area.lessons.filter(l => l.found > 0).length

          return (
            <button
              key={area.name}
              onClick={() => handleAreaClick(area.name)}
              className={`p-4 rounded-2xl border text-left transition-all hover:shadow-md ${
                isActive ? `${cfg.bg} ${cfg.border} shadow-md` : 'bg-surface-50 border-surface-200 hover:border-surface-300'
              }`}
            >
              <p className={`text-xs font-bold mb-2 ${isActive ? cfg.color : 'text-gray-500'}`}>
                {area.name}
              </p>
              <p className={`text-2xl font-bold mb-0.5 ${isActive ? cfg.color : 'text-white'}`}>
                {area.found_total}
              </p>
              <p className="text-[11px] text-gray-500 mb-3">soru bulundu</p>
              <div className="space-y-1.5">
                <div className="flex justify-between text-[10px] text-gray-600">
                  <span>{lessonsWithData}/{area.lessons.length} ders</span>
                  {successRate > 0 && <span>%{successRate}</span>}
                </div>
                <div className="w-full bg-surface-200 rounded-full h-1">
                  <div className={`h-1 rounded-full transition-all ${cfg.barColor}`} style={{ width: `${successRate}%` }} />
                </div>
              </div>
            </button>
          )
        })}
      </div>

      {/* Lesson panel */}
      {currentArea && !showAreaAnalysis && (
        <LessonPanel
          area={currentArea}
          yearFilter={yearFilter}
          generatingTopic={generatingTopic}
          onGenerate={handleGenerate}
          onAreaAnalyze={handleAreaAnalyze}
        />
      )}

      {/* Area-level analysis */}
      {showAreaAnalysis && selectedArea && (
        areaAnalysisLoading ? (
          <div className="flex justify-center py-8"><Spinner size={6} /></div>
        ) : areaAnalysis ? (
          <AreaAnalysisPanel
            areaName={selectedArea}
            data={areaAnalysis}
            onBack={() => { setShowAreaAnalysis(false); setAreaAnalysis(null) }}
            generatingTopic={generatingTopic}
            onGenerate={handleGenerate}
          />
        ) : null
      )}

      {!selectedArea && !loading && (
        <div className="flex flex-col items-center justify-center py-12 text-center text-gray-600">
          <BarChart2 size={32} className="mb-3 text-gray-700" />
          <p className="text-sm">Bir alana tıklayarak ders ve konu analizini görün</p>
        </div>
      )}
    </div>
  )
}

// ── Upload Tab ────────────────────────────────────────────────
function UploadTab({ onUploaded }: { onUploaded: () => void }) {
  const [phase, setPhase] = useState<'idle' | 'uploading'>('idle')
  const [savedAnalyses, setSavedAnalyses] = useState<SgsAnalysisMeta[]>([])
  const [loadingList, setLoadingList] = useState(true)
  const [uploadMeta, setUploadMeta] = useState({
    document_type: SGS_DOCUMENT_TYPES[0] as string,
    year: '',
    semester: '',
  })

  useEffect(() => {
    sgsService.listAnalyses()
      .then(setSavedAnalyses).catch(() => {}).finally(() => setLoadingList(false))
  }, [])

  const handleFileChange = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setPhase('uploading')
    try {
      const result = await sgsService.analyzePdf(file, uploadMeta)
      const list = await sgsService.listAnalyses()
      setSavedAnalyses(list)
      if (result.analysis_id) {
        try {
          const pr = await sgsService.parseQuestions({ analysis_id: result.analysis_id })
          if (pr.questions_created > 0) {
            toast.success(`${pr.questions_created} soru kaydedildi`)
          } else {
            toast.success('PDF analiz edildi')
          }
        } catch { toast.success('PDF analiz edildi') }
      }
      onUploaded()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
        ?? (err as { message?: string })?.message ?? 'Yükleme başarısız'
      toast.error(msg)
    } finally {
      setPhase('idle')
      e.target.value = ''
    }
  }, [uploadMeta, onUploaded])

  const handleDelete = async (id: string) => {
    try {
      await sgsService.deleteAnalysis(id)
      setSavedAnalyses(prev => prev.filter(a => a.id !== id))
    } catch { toast.error('Silinemedi') }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-4">
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
              type="text" placeholder="örn: 2025"
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

        <label
          htmlFor="sgs-pdf-input"
          className={`block border-2 border-dashed rounded-2xl p-10 text-center transition-all ${
            phase === 'uploading'
              ? 'border-brand-500/30 cursor-not-allowed'
              : 'border-surface-300 cursor-pointer hover:border-brand-500/50 hover:bg-brand-500/5'
          }`}
        >
          <input
            id="sgs-pdf-input" type="file" accept=".pdf,application/pdf"
            className="hidden" onChange={handleFileChange} disabled={phase === 'uploading'}
          />
          {phase === 'uploading' ? (
            <div className="flex flex-col items-center gap-3">
              <Spinner size={10} />
              <p className="text-sm text-brand-300 font-medium">PDF işleniyor...</p>
              <p className="text-xs text-gray-500">Sorular çıkarılıyor ve kaydediliyor</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <div className="w-16 h-16 rounded-2xl bg-brand-600/10 flex items-center justify-center">
                <Upload size={28} className="text-brand-400" />
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-200">SGS sınav PDF&apos;i yükle</p>
                <p className="text-xs text-gray-500 mt-1">
                  Sorular otomatik çıkarılır, sınıflandırılır ve veritabanına kaydedilir
                </p>
              </div>
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-100 border border-surface-200 text-sm text-gray-300">
                <FileText size={14} /> PDF Seç
              </span>
            </div>
          )}
        </label>
      </div>

      {!loadingList && savedAnalyses.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
            <Clock size={13} className="text-gray-500" />
            Yüklenen PDF&apos;ler ({savedAnalyses.length})
          </h3>
          <div className="space-y-2">
            {savedAnalyses.map(a => (
              <div key={a.id} className="flex items-center justify-between p-4 bg-surface-50 rounded-xl border border-surface-200">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 rounded-lg bg-surface-200 flex items-center justify-center shrink-0">
                    <FileText size={14} className="text-gray-500" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm text-gray-200 font-medium truncate">{a.pdf_name}</p>
                    <p className="text-xs text-gray-500">
                      {a.document_type && <span>{a.document_type}</span>}
                      {a.year && <> · {a.year}</>}
                      {a.semester && <> · {a.semester}</>}
                      {' · '}{a.total_questions} soru
                      {' · '}{new Date(a.created_at).toLocaleDateString('tr-TR')}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(a.id)}
                  className="p-1.5 text-gray-600 hover:text-red-400 transition-colors shrink-0 ml-3"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {!loadingList && savedAnalyses.length === 0 && phase === 'idle' && (
        <div className="flex flex-col items-center justify-center py-8 text-center text-gray-600">
          <GraduationCap size={28} className="mb-2 text-gray-700" />
          <p className="text-sm">Henüz PDF yüklenmedi.</p>
        </div>
      )}
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────
export default function AcademyPage() {
  const [pageTab, setPageTab] = useState<PageTab>('dashboard')
  const [reloadKey, setReloadKey] = useState(0)

  const handleUploaded = () => {
    setReloadKey(k => k + 1)
    setPageTab('dashboard')
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
              Sınav Analiz Merkezi — PDF yükle, konuları otomatik analiz et, içerik üret
            </p>
          </div>
          <div className="flex gap-1 bg-surface-100 p-1 rounded-xl">
            <button
              onClick={() => setPageTab('dashboard')}
              className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                pageTab === 'dashboard' ? 'bg-surface-50 text-white shadow-sm' : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              <BarChart2 size={13} /> Alan Analizi
            </button>
            <button
              onClick={() => setPageTab('upload')}
              className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                pageTab === 'upload' ? 'bg-surface-50 text-white shadow-sm' : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              <Upload size={13} /> PDF Yükle
            </button>
          </div>
        </div>

        {pageTab === 'dashboard' && <DashboardTab reloadKey={reloadKey} />}
        {pageTab === 'upload' && <UploadTab onUploaded={handleUploaded} />}
      </div>
    </AppShell>
  )
}
