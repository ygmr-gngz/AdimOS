'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import AppShell from '@/components/layout/AppShell'
import Button from '@/components/ui/Button'
import toast from 'react-hot-toast'
import {
  Film, Plus, X, ChevronRight, CheckCircle, XCircle,
  Clock, RefreshCw, AlertTriangle, Loader2,
} from 'lucide-react'
import videoService, {
  VideoJob, VideoScene, VideoStatus, VideoType, VideoFormat,
  CreateVideoPayload, VIDEO_STATUS_LABELS, VIDEO_STATUS_COLORS, VIDEO_TYPE_LABELS,
} from '@/services/video.service'

// ── Durum badge ───────────────────────────────────────────────

function StatusBadge({ status }: { status: VideoStatus }) {
  const label = VIDEO_STATUS_LABELS[status]
  const color = VIDEO_STATUS_COLORS[status]
  const isSpinning = ['scripting', 'tts_generating', 'rendering'].includes(status)
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      padding: '4px 12px', borderRadius: 20, fontSize: 13, fontWeight: 600,
      background: `${color}15`, color,
    }}>
      {isSpinning
        ? <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} />
        : status === 'approved' ? <CheckCircle size={12} />
        : status === 'failed' || status === 'rejected' ? <XCircle size={12} />
        : <Clock size={12} />}
      {label}
    </span>
  )
}

// ── Pipeline ─────────────────────────────────────────────────

const PIPELINE_STEPS: { key: VideoStatus; label: string }[] = [
  { key: 'scripting', label: 'Senaryo' },
  { key: 'tts_generating', label: 'Ses' },
  { key: 'rendering', label: 'Render' },
  { key: 'ready_for_review', label: 'İnceleme' },
]

const STATUS_ORDER: VideoStatus[] = [
  'pending', 'scripting', 'tts_generating', 'rendering', 'ready_for_review', 'approved', 'rejected', 'failed',
]

function PipelineBar({ status }: { status: VideoStatus }) {
  const currentIdx = STATUS_ORDER.indexOf(status)
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 10 }}>
      {PIPELINE_STEPS.map((step, i) => {
        const stepIdx = STATUS_ORDER.indexOf(step.key)
        const done = currentIdx > stepIdx
        const active = currentIdx === stepIdx
        const color = done ? '#10b981' : active ? '#3b82f6' : '#e2e8f0'
        return (
          <div key={step.key} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{
              width: 10, height: 10, borderRadius: '50%',
              background: color,
              boxShadow: active ? `0 0 0 3px ${color}30` : 'none',
            }} />
            <span style={{ fontSize: 12, color: done || active ? '#475569' : '#94a3b8', fontWeight: active ? 600 : 400 }}>
              {step.label}
            </span>
            {i < PIPELINE_STEPS.length - 1 && (
              <div style={{ width: 24, height: 1.5, background: done ? '#10b981' : '#e2e8f0' }} />
            )}
          </div>
        )
      })}
    </div>
  )
}

// ── Video Önizleme Modalı ─────────────────────────────────────

function PreviewModal({ job, onClose, onApprove, onReject }: {
  job: VideoJob
  onClose: () => void
  onApprove: () => void
  onReject: () => void
}) {
  const [rejectReason, setRejectReason] = useState('')
  const [showRejectInput, setShowRejectInput] = useState(false)
  const [regeneratingScene, setRegeneratingScene] = useState<string | null>(null)

  const handleRegenScene = async (scene: VideoScene) => {
    setRegeneratingScene(scene.id)
    try {
      await videoService.regenerateScene(scene.id)
      toast.success(`Sahne ${scene.scene_index + 1} yeniden üretiliyor`)
    } catch {
      toast.error('Sahne yeniden üretilemedi')
    } finally {
      setRegeneratingScene(null)
    }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, padding: 24,
    }}>
      <div style={{
        background: '#fff', borderRadius: 20, width: '90%', maxWidth: 1000,
        maxHeight: '90vh', overflow: 'hidden', display: 'flex', flexDirection: 'column',
        boxShadow: '0 32px 80px rgba(0,0,0,0.3)',
      }}>
        {/* Header */}
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '20px 28px', borderBottom: '1px solid #f1f5f9',
        }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: '#0B2A4A' }}>
              {job.title}
            </h2>
            <p style={{ margin: '4px 0 0', fontSize: 13, color: '#64748b' }}>
              {VIDEO_TYPE_LABELS[job.type]} · {job.lesson_name} · {job.topic}
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <StatusBadge status={job.status} />
            <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>
              <X size={22} />
            </button>
          </div>
        </div>

        {/* İçerik */}
        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          {/* Video player */}
          <div style={{
            flex: 3, background: '#0B2A4A', display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: 24, minHeight: 360,
          }}>
            {job.video_url ? (
              <video
                src={job.video_url}
                controls
                style={{ maxWidth: '100%', maxHeight: 400, borderRadius: 12 }}
              />
            ) : (
              <div style={{ textAlign: 'center', color: '#94a3b8' }}>
                {['rendering', 'tts_generating', 'scripting'].includes(job.status) ? (
                  <>
                    <Loader2 size={48} style={{ animation: 'spin 1s linear infinite', marginBottom: 16 }} />
                    <p style={{ fontSize: 16, margin: 0 }}>Video üretiliyor...</p>
                    <PipelineBar status={job.status} />
                  </>
                ) : (
                  <>
                    <Film size={48} style={{ marginBottom: 12, opacity: 0.4 }} />
                    <p style={{ fontSize: 15, margin: 0, opacity: 0.6 }}>Video henüz hazır değil</p>
                    {job.error_message && (
                      <div style={{
                        marginTop: 12, padding: '10px 14px',
                        background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.25)',
                        borderRadius: 10, maxWidth: 320, textAlign: 'left',
                      }}>
                        <p style={{ margin: '0 0 4px', fontSize: 11, fontWeight: 700, color: '#ef4444', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                          Render Hatası
                        </p>
                        <p style={{ margin: 0, fontSize: 12, color: '#fca5a5', lineHeight: 1.5 }}>
                          {job.error_message}
                        </p>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>

          {/* Sahne listesi */}
          <div style={{
            flex: 2, overflow: 'auto', padding: 20, borderLeft: '1px solid #f1f5f9',
          }}>
            <p style={{ fontSize: 13, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, margin: '0 0 12px' }}>
              Sahneler ({job.scenes?.length ?? 0})
            </p>
            {job.scenes?.map((scene, i) => (
              <div key={scene.id} style={{
                border: '1px solid #e2e8f0', borderRadius: 10, padding: '12px 14px',
                marginBottom: 8, background: '#fafafa',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ margin: 0, fontSize: 13, fontWeight: 600, color: '#0B2A4A' }}>
                      {i + 1}. {scene.component}
                    </p>
                    <p style={{ margin: '4px 0 0', fontSize: 12, color: '#94a3b8' }}>
                      {scene.duration_seconds}s
                      {scene.tts_url ? ' · Ses hazır' : ' · Ses yok'}
                    </p>
                    {scene.voice_text && (
                      <p style={{
                        margin: '6px 0 0', fontSize: 12, color: '#475569',
                        display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                      }}>
                        {scene.voice_text}
                      </p>
                    )}
                    {scene.tts_url && (
                      <audio
                        controls
                        src={scene.tts_url}
                        style={{ marginTop: 8, width: '100%', height: 28 }}
                      />
                    )}
                  </div>
                  {job.status === 'ready_for_review' && (
                    <button
                      onClick={() => handleRegenScene(scene)}
                      disabled={regeneratingScene === scene.id}
                      style={{
                        border: '1px solid #e2e8f0', background: '#fff', borderRadius: 8,
                        padding: '4px 10px', cursor: 'pointer', fontSize: 12, color: '#475569',
                        display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0, marginLeft: 8,
                      }}
                    >
                      <RefreshCw size={11} style={{ animation: regeneratingScene === scene.id ? 'spin 1s linear infinite' : 'none' }} />
                      Yeniden üret
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Alt butonlar */}
        {job.status === 'ready_for_review' && (
          <div style={{
            padding: '16px 28px', borderTop: '1px solid #f1f5f9',
            display: 'flex', gap: 12, alignItems: 'center',
          }}>
            {showRejectInput ? (
              <>
                <input
                  value={rejectReason}
                  onChange={e => setRejectReason(e.target.value)}
                  placeholder="Red sebebi (isteğe bağlı)..."
                  style={{
                    flex: 1, border: '1.5px solid #e2e8f0', borderRadius: 10,
                    padding: '10px 14px', fontSize: 14, outline: 'none',
                  }}
                  autoFocus
                />
                <Button
                  variant="secondary"
                  onClick={() => { onReject(); setShowRejectInput(false) }}
                >
                  Reddet
                </Button>
                <button onClick={() => setShowRejectInput(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>
                  İptal
                </button>
              </>
            ) : (
              <>
                <Button onClick={onApprove} style={{ background: '#10b981', color: '#fff', border: 'none' }}>
                  <CheckCircle size={16} /> Onayla
                </Button>
                <Button variant="secondary" onClick={() => setShowRejectInput(true)}>
                  <XCircle size={16} /> Reddet
                </Button>
                <Button variant="secondary" onClick={() => videoService.regenerateJob(job.id).then(() => toast.success('Yeniden üretiliyor'))}>
                  <RefreshCw size={16} /> Tümünü yeniden üret
                </Button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Video oluşturma modalı ────────────────────────────────────

const QUIZ_OPTION_LABELS = ['A', 'B', 'C', 'D']

// Tip bazlı konfigürasyon
const TYPE_CONFIG: Record<VideoType, {
  needsLesson: boolean
  needsTopic: boolean
  topicLabel: string
  descriptionPlaceholder: string
  defaultFormat: VideoFormat
  defaultMinutes: number
}> = {
  lesson: {
    needsLesson: true, needsTopic: true,
    topicLabel: 'Konu',
    descriptionPlaceholder: 'Bu derste özellikle hangi konu anlatılsın? Ton veya tarz notu ekleyebilirsin.',
    defaultFormat: '16:9', defaultMinutes: 25,
  },
  quiz: {
    needsLesson: true, needsTopic: true,
    topicLabel: 'Konu / Soru Tipi',
    descriptionPlaceholder: 'Hangi soru tipleri çözülsün? Özel not ekleyebilirsin.',
    defaultFormat: '16:9', defaultMinutes: 15,
  },
  motivation: {
    needsLesson: false, needsTopic: false,
    topicLabel: 'Video Teması (isteğe bağlı)',
    descriptionPlaceholder: 'İstersen video temasını yazabilirsin. Boş bırakırsan sistem otomatik oluşturacaktır.',
    defaultFormat: '16:9', defaultMinutes: 3,
  },
  shorts: {
    needsLesson: false, needsTopic: false,
    topicLabel: 'Konu (isteğe bağlı)',
    descriptionPlaceholder: 'Trend olabilecek kısa içerik fikri yazabilir veya boş bırakabilirsin.',
    defaultFormat: '9:16', defaultMinutes: 1,
  },
}

const INPUT_STYLE: React.CSSProperties = {
  width: '100%', border: '1.5px solid #e2e8f0', borderRadius: 10,
  padding: '12px 14px', fontSize: 15, outline: 'none',
  boxSizing: 'border-box', color: '#0f172a', background: '#fff',
}

function CreateVideoModal({ onClose, onCreated }: { onClose: () => void; onCreated: (job: VideoJob) => void }) {
  const [step, setStep] = useState<'config' | 'questions'>('config')
  const [type, setType] = useState<VideoType>('quiz')
  const [title, setTitle] = useState('')
  const [lessonName, setLessonName] = useState('')
  const [topic, setTopic] = useState('')
  const [description, setDescription] = useState('')
  const [format, setFormat] = useState<VideoFormat>('16:9')
  const [targetMinutes, setTargetMinutes] = useState(15)
  const [loading, setLoading] = useState(false)

  const cfg = TYPE_CONFIG[type]

  // Tip değişince format/süre sıfırla
  const handleTypeChange = (t: VideoType) => {
    setType(t)
    setFormat(TYPE_CONFIG[t].defaultFormat)
    setTargetMinutes(TYPE_CONFIG[t].defaultMinutes)
  }

  const [questions, setQuestions] = useState<CreateVideoPayload['questions']>([
    { text: '', options: QUIZ_OPTION_LABELS.map(l => ({ label: l, text: '' })), correct_label: 'A', explanation: '' },
    { text: '', options: QUIZ_OPTION_LABELS.map(l => ({ label: l, text: '' })), correct_label: 'A', explanation: '' },
    { text: '', options: QUIZ_OPTION_LABELS.map(l => ({ label: l, text: '' })), correct_label: 'A', explanation: '' },
    { text: '', options: QUIZ_OPTION_LABELS.map(l => ({ label: l, text: '' })), correct_label: 'A', explanation: '' },
  ])

  const updateQuestion = (qi: number, field: string, value: string) => {
    setQuestions(prev => {
      const next = [...(prev ?? [])]
      next[qi] = { ...next[qi], [field]: value } as typeof next[0]
      return next
    })
  }

  const updateOption = (qi: number, oi: number, value: string) => {
    setQuestions(prev => {
      const next = [...(prev ?? [])]
      const opts = [...next[qi].options]
      opts[oi] = { ...opts[oi], text: value }
      next[qi] = { ...next[qi], options: opts }
      return next
    })
  }

  const validate = (): boolean => {
    if (cfg.needsLesson && !lessonName.trim()) {
      toast.error('Ders adı zorunludur')
      return false
    }
    if (cfg.needsTopic && !topic.trim()) {
      toast.error('Konu zorunludur')
      return false
    }
    return true
  }

  const handleSubmit = async () => {
    if (!validate()) return
    setLoading(true)
    try {
      const autoTitle = title.trim() ||
        (type === 'motivation' ? 'Motivasyon Videosu' :
         type === 'shorts' ? 'Kısa İçerik' :
         `${lessonName} — ${topic}`)
      const job = await videoService.createJob({
        type,
        title: autoTitle,
        lesson_name: lessonName.trim() || undefined,
        topic: topic.trim() || undefined,
        description: description.trim() || undefined,
        format,
        target_duration_minutes: targetMinutes,
        questions: type === 'quiz' ? questions : undefined,
      })
      toast.success('Video üretim görevi başlatıldı!')
      onCreated(job)
      onClose()
    } catch {
      toast.error('Görev oluşturulamadı')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, padding: 24,
    }}>
      <div style={{
        background: '#fff', borderRadius: 20, width: '100%', maxWidth: 760,
        maxHeight: '90vh', overflow: 'hidden', display: 'flex', flexDirection: 'column',
        boxShadow: '0 24px 64px rgba(0,0,0,0.2)',
      }}>
        {/* Header */}
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '20px 28px', borderBottom: '1px solid #f1f5f9',
        }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: '#0B2A4A' }}>
            {step === 'config' ? 'Yeni Video Görevi' : 'Soruları Girin'}
          </h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>
            <X size={22} />
          </button>
        </div>

        <div style={{ overflow: 'auto', flex: 1 }}>
          {step === 'config' ? (
            <div style={{ padding: 28, display: 'flex', flexDirection: 'column', gap: 20 }}>

              {/* Video tipi */}
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 8 }}>Video Tipi</label>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  {(['quiz', 'lesson', 'motivation', 'shorts'] as VideoType[]).map(t => (
                    <button key={t} onClick={() => handleTypeChange(t)} style={{
                      padding: '10px 20px', borderRadius: 10, cursor: 'pointer',
                      border: `2px solid ${type === t ? '#0B2A4A' : '#e2e8f0'}`,
                      background: type === t ? '#0B2A4A' : '#fff',
                      color: type === t ? '#fff' : '#475569',
                      fontSize: 14, fontWeight: 600, transition: 'all 0.15s',
                    }}>
                      {VIDEO_TYPE_LABELS[t]}
                    </button>
                  ))}
                </div>
              </div>

              {/* Başlık (eğitim tiplerinde göster, diğerlerinde opsiyonel açıklama olarak) */}
              {(cfg.needsLesson) && (
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 8 }}>
                    Başlık <span style={{ color: '#94a3b8', fontWeight: 400 }}>(boş bırakılırsa otomatik oluşturulur)</span>
                  </label>
                  <input value={title} onChange={e => setTitle(e.target.value)}
                    placeholder={`Örn: ${type === 'quiz' ? 'SGS 2024 — KDV Soru Çözümü' : 'Vergi Hukuku — KDV Konu Anlatımı'}`}
                    style={INPUT_STYLE} />
                </div>
              )}

              {/* Ders + konu — sadece eğitim tiplerinde */}
              {cfg.needsLesson && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <div>
                    <label style={{ fontSize: 13, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 8 }}>
                      Ders Adı <span style={{ color: '#ef4444' }}>*</span>
                    </label>
                    <input value={lessonName} onChange={e => setLessonName(e.target.value)}
                      placeholder="Örn: Vergi Hukuku" style={INPUT_STYLE} />
                  </div>
                  <div>
                    <label style={{ fontSize: 13, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 8 }}>
                      {cfg.topicLabel} <span style={{ color: '#ef4444' }}>*</span>
                    </label>
                    <input value={topic} onChange={e => setTopic(e.target.value)}
                      placeholder="Örn: Katma Değer Vergisi" style={INPUT_STYLE} />
                  </div>
                </div>
              )}

              {/* Konu — motivasyon/shorts için opsiyonel */}
              {!cfg.needsLesson && (
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 8 }}>
                    {cfg.topicLabel}
                  </label>
                  <input value={topic} onChange={e => setTopic(e.target.value)}
                    placeholder={
                      type === 'motivation'
                        ? 'Örn: Hedeflerine ulaşmak için vazgeçmemenin önemi'
                        : 'Örn: Vergi, kariyer, yapay zeka...'
                    }
                    style={INPUT_STYLE} />
                </div>
              )}

              {/* Açıklama / Not — tüm tipler için opsiyonel */}
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 8 }}>
                  Açıklama / Yönetmen Notu
                  <span style={{ color: '#94a3b8', fontWeight: 400 }}> — opsiyonel</span>
                </label>
                <textarea
                  value={description} onChange={e => setDescription(e.target.value)}
                  placeholder={cfg.descriptionPlaceholder}
                  rows={3}
                  style={{
                    ...INPUT_STYLE, resize: 'vertical', lineHeight: 1.6,
                    color: '#0f172a',
                  }}
                />
              </div>

              {/* Format + süre */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 8 }}>Format</label>
                  <div style={{ display: 'flex', gap: 10 }}>
                    {(['16:9', '9:16'] as VideoFormat[]).map(f => (
                      <button key={f} onClick={() => setFormat(f)} style={{
                        flex: 1, padding: '10px', borderRadius: 10, cursor: 'pointer',
                        border: `2px solid ${format === f ? '#0B2A4A' : '#e2e8f0'}`,
                        background: format === f ? '#0B2A4A' : '#fff',
                        color: format === f ? '#fff' : '#475569',
                        fontSize: 13, fontWeight: 600,
                      }}>
                        {f === '16:9' ? '16:9 (Yatay)' : '9:16 (Dikey)'}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 8 }}>
                    Hedef Süre (dakika)
                  </label>
                  <input type="number" min={1} max={60}
                    value={targetMinutes} onChange={e => setTargetMinutes(Number(e.target.value))}
                    style={{ ...INPUT_STYLE }} />
                </div>
              </div>
            </div>
          ) : (
            /* Sorular adımı — yalnızca quiz tipi */
            <div style={{ padding: 28 }}>
              <p style={{ margin: '0 0 20px', fontSize: 14, color: '#64748b' }}>
                Soruları girin. Boş bırakırsanız backend konuya göre otomatik oluşturur.
              </p>
              {questions?.map((q, qi) => (
                <div key={qi} style={{ border: '1.5px solid #e2e8f0', borderRadius: 14, padding: 20, marginBottom: 16 }}>
                  <p style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 700, color: '#0B2A4A' }}>Soru {qi + 1}</p>
                  <textarea value={q.text} onChange={e => updateQuestion(qi, 'text', e.target.value)}
                    placeholder="Soru metni..." rows={2}
                    style={{ ...INPUT_STYLE, resize: 'vertical', marginBottom: 10 }} />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 10 }}>
                    {q.options.map((opt, oi) => (
                      <div key={opt.label} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <span style={{
                          width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                          background: q.correct_label === opt.label ? '#10b981' : '#0B2A4A',
                          color: '#fff', fontSize: 13, fontWeight: 700,
                          display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
                        }} onClick={() => updateQuestion(qi, 'correct_label', opt.label)}>
                          {opt.label}
                        </span>
                        <input value={opt.text} onChange={e => updateOption(qi, oi, e.target.value)}
                          placeholder={`${opt.label} şıkkı...`}
                          style={{
                            flex: 1, border: `1.5px solid ${q.correct_label === opt.label ? '#10b981' : '#e2e8f0'}`,
                            borderRadius: 8, padding: '8px 12px', fontSize: 14, outline: 'none', color: '#0f172a',
                          }} />
                      </div>
                    ))}
                  </div>
                  <input value={q.explanation ?? ''} onChange={e => updateQuestion(qi, 'explanation', e.target.value)}
                    placeholder="Doğru cevabın açıklaması (opsiyonel)..."
                    style={{ ...INPUT_STYLE, fontSize: 13 }} />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{ padding: '16px 28px', borderTop: '1px solid #f1f5f9', display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
          {step === 'questions' && (
            <Button variant="secondary" onClick={() => setStep('config')}>Geri</Button>
          )}
          {type === 'quiz' && step === 'config' ? (
            <Button onClick={() => { if (validate()) setStep('questions') }}>
              Soruları Gir <ChevronRight size={16} />
            </Button>
          ) : (
            <Button onClick={handleSubmit} disabled={loading}>
              {loading
                ? <><Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} /> Oluşturuluyor...</>
                : 'Video Görevi Başlat'}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Ana Sayfa ─────────────────────────────────────────────────

export default function VideoPage() {
  const router = useRouter()
  const [jobs, setJobs] = useState<VideoJob[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<VideoType | 'all'>('all')
  const [showCreate, setShowCreate] = useState(false)
  const [previewJob, setPreviewJob] = useState<VideoJob | null>(null)
  const pollRef = useRef<NodeJS.Timeout | null>(null)

  const loadJobs = async () => {
    try {
      const data = await videoService.listJobs(filter === 'all' ? undefined : filter)
      setJobs(data)
    } catch {
      // sessiz
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadJobs()
    // Aktif iş varsa her 10 saniyede bir yenile
    pollRef.current = setInterval(() => {
      const hasActive = jobs.some(j => ['scripting', 'tts_generating', 'rendering'].includes(j.status))
      if (hasActive) loadJobs()
    }, 10000)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter])

  const handleApprove = async (job: VideoJob) => {
    try {
      await videoService.approveJob(job.id)
      toast.success('Video onaylandı — İçerik Otomasyonuna yönlendiriliyor')
      setPreviewJob(null)
      loadJobs()
      setTimeout(() => router.push('/automation'), 1500)
    } catch { toast.error('Onaylama başarısız') }
  }

  const handleReject = async (job: VideoJob) => {
    try {
      await videoService.rejectJob(job.id)
      toast.success('Video reddedildi')
      setPreviewJob(null)
      loadJobs()
    } catch { toast.error('Reddetme başarısız') }
  }

  const pendingReview = jobs.filter(j => j.status === 'ready_for_review')
  const activeJobs = jobs.filter(j => ['scripting', 'tts_generating', 'rendering'].includes(j.status))

  return (
    <AppShell>
      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '32px 24px' }}>
        {/* Başlık */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 32 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
              <Film size={26} color="#0B2A4A" />
              <h1 style={{ margin: 0, fontSize: 28, fontWeight: 800, color: '#0B2A4A' }}>Video Prodüksiyon</h1>
            </div>
            <p style={{ margin: 0, color: '#64748b', fontSize: 15 }}>
              AI destekli eğitim videosu üretim motoru
            </p>
          </div>
          <Button onClick={() => setShowCreate(true)}>
            <Plus size={16} /> Yeni Video Görevi
          </Button>
        </div>

        {/* Özet kartlar */}
        {(pendingReview.length > 0 || activeJobs.length > 0) && (
          <div style={{ display: 'flex', gap: 12, marginBottom: 28, flexWrap: 'wrap' }}>
            {activeJobs.length > 0 && (
              <div style={{
                flex: 1, minWidth: 200, background: '#eff6ff', border: '1.5px solid #bfdbfe',
                borderRadius: 14, padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 12,
              }}>
                <Loader2 size={20} color="#3b82f6" style={{ animation: 'spin 1s linear infinite' }} />
                <div>
                  <p style={{ margin: 0, fontSize: 14, fontWeight: 700, color: '#1d4ed8' }}>
                    {activeJobs.length} Video Üretiliyor
                  </p>
                  <p style={{ margin: 0, fontSize: 12, color: '#3b82f6' }}>Otomatik yenileniyor</p>
                </div>
              </div>
            )}
            {pendingReview.length > 0 && (
              <div style={{
                flex: 1, minWidth: 200, background: '#f5f3ff', border: '1.5px solid #ddd6fe',
                borderRadius: 14, padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 12,
              }}>
                <AlertTriangle size={20} color="#7c3aed" />
                <div>
                  <p style={{ margin: 0, fontSize: 14, fontWeight: 700, color: '#6d28d9' }}>
                    {pendingReview.length} Video İnceleme Bekliyor
                  </p>
                  <p style={{ margin: 0, fontSize: 12, color: '#7c3aed' }}>Onayla veya reddet</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Filtreler */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
          {(['all', 'quiz', 'lesson', 'shorts', 'motivation'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                padding: '7px 16px', borderRadius: 20, cursor: 'pointer', fontSize: 13, fontWeight: 600,
                border: `1.5px solid ${filter === f ? '#0B2A4A' : '#e2e8f0'}`,
                background: filter === f ? '#0B2A4A' : '#fff',
                color: filter === f ? '#fff' : '#475569',
              }}
            >
              {f === 'all' ? 'Tümü' : VIDEO_TYPE_LABELS[f]}
            </button>
          ))}
        </div>

        {/* İş listesi */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>
            <Loader2 size={36} style={{ animation: 'spin 1s linear infinite', marginBottom: 12 }} />
            <p>Yükleniyor...</p>
          </div>
        ) : jobs.length === 0 ? (
          <div style={{
            textAlign: 'center', padding: 80, border: '2px dashed #e2e8f0',
            borderRadius: 16, color: '#94a3b8',
          }}>
            <Film size={48} style={{ marginBottom: 16, opacity: 0.3 }} />
            <p style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Henüz video yok</p>
            <p style={{ fontSize: 14 }}>İlk video görevinizi başlatmak için &quot;Yeni Video Görevi&quot; butonuna tıklayın.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {jobs.map(job => (
              <div
                key={job.id}
                style={{
                  background: '#fff', border: '1.5px solid #e2e8f0',
                  borderRadius: 16, padding: '20px 24px',
                  display: 'flex', alignItems: 'flex-start', gap: 20,
                  cursor: 'pointer', transition: 'box-shadow 0.15s',
                  boxShadow: job.status === 'ready_for_review' ? '0 0 0 2px #8b5cf6' : 'none',
                }}
                onClick={async () => {
                  const full = await videoService.getJob(job.id)
                  setPreviewJob(full)
                }}
              >
                {/* Tip ikonu */}
                <div style={{
                  width: 48, height: 48, borderRadius: 12, flexShrink: 0,
                  background: '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <Film size={22} color="#0B2A4A" />
                </div>

                {/* Bilgiler */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4, flexWrap: 'wrap' }}>
                    <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#0B2A4A' }}>
                      {job.title}
                    </h3>
                    <StatusBadge status={job.status} />
                  </div>
                  <p style={{ margin: '0 0 6px', fontSize: 13, color: '#64748b' }}>
                    {VIDEO_TYPE_LABELS[job.type]} · {job.lesson_name} · {job.topic}
                    · {job.format} · {job.target_duration_minutes} dk
                  </p>
                  {['scripting', 'tts_generating', 'rendering'].includes(job.status) && (
                    <PipelineBar status={job.status} />
                  )}
                  {job.error_message && (
                    <p style={{ margin: '6px 0 0', fontSize: 12, color: '#ef4444' }}>
                      Hata: {job.error_message}
                    </p>
                  )}
                </div>

                {/* Sağ ok */}
                <ChevronRight size={18} color="#94a3b8" style={{ flexShrink: 0, marginTop: 4 }} />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modaller */}
      {showCreate && (
        <CreateVideoModal
          onClose={() => setShowCreate(false)}
          onCreated={job => {
            setJobs(prev => [job, ...prev])
            loadJobs()
          }}
        />
      )}
      {previewJob && (
        <PreviewModal
          job={previewJob}
          onClose={() => setPreviewJob(null)}
          onApprove={() => handleApprove(previewJob)}
          onReject={() => handleReject(previewJob)}
        />
      )}
    </AppShell>
  )
}
