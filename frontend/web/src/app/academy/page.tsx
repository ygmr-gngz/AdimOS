'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import AppShell from '@/components/layout/AppShell'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import {
  GraduationCap, Upload, FileText, Play, ChevronDown,
  ChevronUp, Clock, BookOpen, Video, Trash2, RefreshCw
} from 'lucide-react'
import { sgsService, type SgsAnalysis, type SgsAnalysisMeta } from '@/services/sgs.service'

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

function VideoPlanCard({
  item,
  index,
  analysisId,
  onGenerate,
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
            <Button
              size="sm"
              variant="secondary"
              onClick={handleGenerate}
              isLoading={generating}
              disabled={!analysisId || generating}
            >
              <Play size={13} />
              Üret
            </Button>
          )}
          <button
            onClick={() => setOpen(!open)}
            className="p-1.5 text-gray-500 hover:text-gray-300 transition-colors"
          >
            {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </div>

      {open && (
        <div className="border-t border-surface-200 p-4 space-y-2">
          <p className="text-xs text-gray-400">{item.description}</p>
          <div className="flex flex-wrap gap-2 mt-2">
            <span className="text-xs bg-surface-200 text-gray-400 px-2 py-0.5 rounded-full">
              Konu: {item.topic}
            </span>
            <span className="text-xs bg-surface-200 text-gray-400 px-2 py-0.5 rounded-full">
              {item.question_ids.length} soru (ID: {item.question_ids.join(', ')})
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

function AnalysisResult({
  analysis,
  onGenerate,
}: {
  analysis: SgsAnalysis
  onGenerate: (idx: number, title: string) => void
}) {
  const [tab, setTab] = useState<'plan' | 'questions'>('plan')
  const [subjFilter, setSubjFilter] = useState<string>('Tümü')

  const subjects = Array.from(new Set(analysis.questions.map(q => q.subject)))
  const filteredQ = subjFilter === 'Tümü'
    ? analysis.questions
    : analysis.questions.filter(q => q.subject === subjFilter)

  return (
    <div className="space-y-5">
      {/* Özet kartlar */}
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
        <div className="bg-surface-50 rounded-xl p-4 border border-surface-200 text-center">
          <p className="text-lg font-bold text-white">
            {analysis.subjects.reduce((a, s) => a + s.topics.length, 0)}
          </p>
          <p className="text-xs text-gray-500 mt-0.5">Konu Başlığı</p>
        </div>
      </div>

      {/* Tab başlıkları */}
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

      {/* Video Planı */}
      {tab === 'plan' && (
        <div className="space-y-3">
          {analysis.video_plan.map((item, idx) => (
            <VideoPlanCard
              key={idx}
              item={item}
              index={idx}
              analysisId={analysis.analysis_id}
              onGenerate={onGenerate}
            />
          ))}
        </div>
      )}

      {/* Soru Bankası */}
      {tab === 'questions' && (
        <div className="space-y-4">
          {/* Ders filtresi */}
          <div className="flex flex-wrap gap-2">
            {['Tümü', ...subjects].map(s => (
              <button
                key={s}
                onClick={() => setSubjFilter(s)}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                  subjFilter === s
                    ? 'bg-brand-600/20 border-brand-500/50 text-brand-300'
                    : 'bg-surface-100 border-surface-200 text-gray-500 hover:text-gray-300'
                }`}
              >
                {s}
              </button>
            ))}
          </div>

          {/* Sorular */}
          <div className="space-y-2">
            {filteredQ.map(q => (
              <QuestionRow key={q.id} question={q} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function QuestionRow({ question }: { question: SgsAnalysis['questions'][0] }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="bg-surface-50 rounded-xl border border-surface-200 overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full text-left p-4 flex items-start gap-3"
      >
        <span className="text-xs font-bold text-gray-600 shrink-0 mt-0.5">#{question.id}</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-gray-200 line-clamp-2">{question.question_text}</p>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-gray-600">{question.subject}</span>
            <span className="text-gray-700">·</span>
            <span className="text-xs text-gray-600">{question.topic}</span>
            {question.year && (
              <>
                <span className="text-gray-700">·</span>
                <span className="text-xs text-gray-600">{question.year}</span>
              </>
            )}
            <span className="text-gray-700">·</span>
            <DiffBadge diff={question.difficulty} />
          </div>
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
                  <span className={`font-bold shrink-0 ${isCorrect ? 'text-green-400' : 'text-gray-600'}`}>
                    {letter})
                  </span>
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

export default function AcademyPage() {
  const [phase, setPhase] = useState<Phase>('idle')
  const [analysis, setAnalysis] = useState<SgsAnalysis | null>(null)
  const [savedAnalyses, setSavedAnalyses] = useState<SgsAnalysisMeta[]>([])
  const [loadingList, setLoadingList] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [generatedTitles, setGeneratedTitles] = useState<string[]>([])
  const fileRef = useRef<HTMLInputElement>(null)

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
      const result = await sgsService.analyzePdf(file)
      setAnalysis(result)
      setPhase('done')
      // Listeyi yenile
      const list = await sgsService.listAnalyses()
      setSavedAnalyses(list)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Bilinmeyen hata'
      setError(msg)
      setPhase('idle')
    }
    e.target.value = ''
  }, [])

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
      if (analysis?.analysis_id === id) {
        setAnalysis(null)
        setPhase('idle')
      }
    } catch {
      setError('Silinemedi')
    }
  }

  const handleGenerate = async (idx: number, title: string) => {
    if (!analysis?.analysis_id) return
    await sgsService.generateVideo(analysis.analysis_id, idx)
    setGeneratedTitles(prev => [...prev, title])
  }

  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in">

        {/* Başlık */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <GraduationCap size={20} className="text-brand-400" />
              SGS Academy
            </h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Çıkmış soru PDF&apos;i yükle → otomatik video serisi planla → üret
            </p>
          </div>
        </div>

        {generatedTitles.length > 0 && (
          <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-xl">
            <p className="text-sm text-green-300 font-medium">
              {generatedTitles.length} video üretimi arka planda başladı.
              Otomasyon sayfasından takip edebilirsiniz.
            </p>
          </div>
        )}

        {/* Upload alanı */}
        {phase !== 'done' && (
          <div
            onClick={() => fileRef.current?.click()}
            className="border-2 border-dashed border-surface-300 rounded-2xl p-10 text-center cursor-pointer hover:border-brand-500/50 hover:bg-brand-500/5 transition-all"
          >
            <input
              ref={fileRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={handleFileChange}
            />
            {phase === 'uploading' ? (
              <div className="flex flex-col items-center gap-3">
                <svg className="animate-spin h-10 w-10 text-brand-400" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <p className="text-sm text-brand-300 font-medium">PDF analiz ediliyor...</p>
                <p className="text-xs text-gray-500">Sorular çıkarılıyor, konulara ayrılıyor, video planı oluşturuluyor</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <div className="w-16 h-16 rounded-2xl bg-brand-600/10 flex items-center justify-center">
                  <Upload size={28} className="text-brand-400" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-200">SGS çıkmış soru PDF&apos;i yükle</p>
                  <p className="text-xs text-gray-500 mt-1">
                    PDF otomatik analiz edilir, sorular konulara göre gruplandırılır,
                    video serisi planı oluşturulur
                  </p>
                </div>
                <Button size="sm" variant="secondary">
                  <FileText size={14} />
                  PDF Seç
                </Button>
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* Analiz sonucu */}
        {phase === 'done' && analysis && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText size={16} className="text-brand-400" />
                <span className="text-sm font-semibold text-white">{analysis.pdf_name}</span>
                <Badge variant="success">Analiz Tamamlandı</Badge>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => { setPhase('idle'); setAnalysis(null) }}
              >
                <RefreshCw size={13} />
                Yeni PDF
              </Button>
            </div>
            <AnalysisResult analysis={analysis} onGenerate={handleGenerate} />
          </div>
        )}

        {/* Kayıtlı analizler */}
        {!loadingList && savedAnalyses.length > 0 && phase !== 'done' && (
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
                        {a.total_questions} soru · {a.video_plan.length} video planı ·{' '}
                        {new Date(a.created_at).toLocaleDateString('tr-TR')}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Button size="sm" variant="secondary" onClick={() => handleLoadSaved(a.id)}>
                      <Video size={13} />
                      Yükle
                    </Button>
                    <button
                      onClick={() => handleDeleteSaved(a.id)}
                      className="p-1.5 text-gray-600 hover:text-red-400 transition-colors"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Hiç analiz yoksa */}
        {!loadingList && savedAnalyses.length === 0 && phase === 'idle' && (
          <div className="flex flex-col items-center justify-center py-10 text-center text-gray-600 text-sm">
            <GraduationCap size={32} className="mb-3 text-gray-700" />
            <p>Henüz analiz yok. Yukarıdan bir PDF yükleyin.</p>
          </div>
        )}

      </div>
    </AppShell>
  )
}
