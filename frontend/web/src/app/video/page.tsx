'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import AppShell from '@/components/layout/AppShell'
import Button from '@/components/ui/Button'
import toast from 'react-hot-toast'
import {
  Film, Plus, X, ChevronRight, CheckCircle, XCircle,
  Clock, RefreshCw, AlertTriangle, Loader2, Image, Zap,
  LayoutGrid, ArrowLeftRight, ListOrdered,
} from 'lucide-react'
import videoService, {
  VideoJob, VideoScene, VideoStatus, VideoType, VideoFormat,
  CreateVideoPayload, VIDEO_STATUS_LABELS, VIDEO_STATUS_COLORS, VIDEO_TYPE_LABELS,
} from '@/services/video.service'

// ── Durum badge ───────────────────────────────────────────────

function StatusBadge({ status }: { status: VideoStatus }) {
  const label = VIDEO_STATUS_LABELS[status]
  const color = VIDEO_STATUS_COLORS[status]
  const isSpinning = ['scripting', 'tts_generating', 'warmup_pinging', 'rendering'].includes(status)
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
  'pending', 'scripting', 'tts_generating', 'warmup_pinging', 'rendering', 'ready_for_review', 'approved', 'rejected', 'failed', 'archived',
]

function PipelineBar({ status }: { status: VideoStatus }) {
  // warmup_pinging → Render adımını aktif göster
  const effectiveStatus: VideoStatus = status === 'warmup_pinging' ? 'rendering' : status
  const currentIdx = STATUS_ORDER.indexOf(effectiveStatus)
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 10 }}>
      {PIPELINE_STEPS.map((step, i) => {
        const stepIdx = STATUS_ORDER.indexOf(step.key === 'rendering' ? 'rendering' : step.key)
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
          {/* Video / görsel player */}
          <div style={{
            flex: 3, background: '#0B2A4A', display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: 24, minHeight: 360,
          }}>
            {job.video_url ? (
              job.type === 'infographic' ? (
                <img
                  src={job.video_url}
                  alt={job.title}
                  style={{ maxWidth: '100%', maxHeight: 500, borderRadius: 12, objectFit: 'contain' }}
                />
              ) : (
                <video
                  src={job.video_url}
                  controls
                  style={{ maxWidth: '100%', maxHeight: 400, borderRadius: 12 }}
                />
              )
            ) : (
              <div style={{ textAlign: 'center', color: '#94a3b8' }}>
                {['rendering', 'tts_generating', 'scripting', 'warmup_pinging'].includes(job.status) ? (
                  <>
                    <Loader2 size={48} style={{ animation: 'spin 1s linear infinite', marginBottom: 16 }} />
                    <p style={{ fontSize: 16, margin: 0 }}>
                      {job.status === 'warmup_pinging'
                        ? 'Render servisi hazırlanıyor...'
                        : 'Video üretiliyor...'}
                    </p>
                    {job.status === 'warmup_pinging' && (
                      <p style={{ fontSize: 13, color: '#0ea5e9', margin: '6px 0 0' }}>
                        Railway render servisi uyanıyor, ~60 saniye bekleyin
                      </p>
                    )}
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

// ── 3 Adımlı Video Sihirbazı ─────────────────────────────────

type WizardStep = 'content' | 'format' | 'review'

const QUIZ_OPTION_LABELS = ['A', 'B', 'C', 'D']

const WIZARD_TYPES: { type: VideoType; label: string; desc: string }[] = [
  { type: 'lesson',      label: 'Konu Anlatımı',  desc: 'Bir konuyu baştan sona anlatan eğitim videosu' },
  { type: 'quiz',        label: 'Soru Çözümü',    desc: 'SGS soruları ile adım adım çözüm videosu' },
  { type: 'shorts',      label: 'Kısa İçerik',    desc: 'Instagram Reels / YouTube Shorts (≤60 sn)' },
  { type: 'motivation',  label: 'Motivasyon',     desc: '15-30 saniye motivasyon klibi, dikey format' },
  { type: 'infographic', label: 'Görsel Post',    desc: 'Anında oluşturulan statik infografik — Remotion gerekmez' },
]

const INFOGRAPHIC_TEMPLATES: { value: string; label: string; desc: string }[] = [
  { value: 'card_grid',  label: 'Kart Izgarası',  desc: 'Kategorilere ayrılmış bilgi kartları' },
  { value: 'comparison', label: 'Karşılaştırma',  desc: 'İki kavramı yan yana karşılaştır' },
  { value: 'process',    label: 'Süreç Adımları', desc: 'Adım adım süreç veya akış' },
]

const TYPE_DEFAULTS: Partial<Record<VideoType, { format: VideoFormat; minutes: number }>> = {
  lesson:      { format: '16:9', minutes: 12 },
  quiz:        { format: '16:9', minutes: 8  },
  shorts:      { format: '9:16', minutes: 1  },
  motivation:  { format: '9:16', minutes: 1  },
  infographic: { format: '9:16', minutes: 1  },
}

const INP: React.CSSProperties = {
  width: '100%', border: '1.5px solid #e2e8f0', borderRadius: 10,
  padding: '11px 14px', fontSize: 14, outline: 'none',
  boxSizing: 'border-box', color: '#0f172a', background: '#fff',
}

function WizardIndicator({ step }: { step: WizardStep }) {
  const steps: { key: WizardStep; label: string }[] = [
    { key: 'content', label: 'İçerik Seç' },
    { key: 'format',  label: 'Format Seç' },
    { key: 'review',  label: 'Üret' },
  ]
  const cur = steps.findIndex(s => s.key === step)
  return (
    <div style={{ display: 'flex', alignItems: 'center', padding: '16px 28px 0', gap: 0 }}>
      {steps.map((s, i) => (
        <div key={s.key} style={{ display: 'flex', alignItems: 'center', flex: i < steps.length - 1 ? 1 : 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
              background: i < cur ? '#10b981' : i === cur ? '#0B2A4A' : '#e2e8f0',
              color: i <= cur ? '#fff' : '#94a3b8',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 12, fontWeight: 700,
            }}>
              {i < cur ? '✓' : i + 1}
            </div>
            <span style={{ fontSize: 13, fontWeight: i === cur ? 600 : 400, color: i === cur ? '#0B2A4A' : '#94a3b8' }}>
              {s.label}
            </span>
          </div>
          {i < steps.length - 1 && (
            <div style={{ flex: 1, height: 1.5, background: i < cur ? '#10b981' : '#e2e8f0', margin: '0 12px' }} />
          )}
        </div>
      ))}
    </div>
  )
}

function CreateVideoModal({ onClose, onCreated }: { onClose: () => void; onCreated: (job: VideoJob) => void }) {
  const [step, setStep] = useState<WizardStep>('content')
  const [type, setType] = useState<VideoType>('lesson')
  const [lessonName, setLessonName] = useState('')
  const [topic, setTopic] = useState('')
  const [infographicTemplate, setInfographicTemplate] = useState('card_grid')
  const [showQuestions, setShowQuestions] = useState(false)
  const [questions, setQuestions] = useState<CreateVideoPayload['questions']>(
    Array.from({ length: 4 }, () => ({
      text: '', correct_label: 'A', explanation: '',
      options: QUIZ_OPTION_LABELS.map(l => ({ label: l, text: '' })),
    }))
  )
  const [format, setFormat] = useState<VideoFormat>('16:9')
  const [targetMinutes, setTargetMinutes] = useState(12)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)

  const handleTypeChange = (t: VideoType) => {
    setType(t)
    const d = TYPE_DEFAULTS[t]
    if (d) { setFormat(d.format); setTargetMinutes(d.minutes) }
  }

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

  const validateContent = () => {
    if (type === 'infographic' || type === 'motivation' || type === 'shorts') {
      if (!topic.trim()) { toast.error('Konu zorunludur'); return false }
      return true
    }
    if (!lessonName.trim()) { toast.error('Ders adı zorunludur'); return false }
    if (!topic.trim()) { toast.error('Konu zorunludur'); return false }
    return true
  }

  const handleSubmit = async () => {
    setLoading(true)
    try {
      let autoTitle = title.trim()
      if (!autoTitle) {
        if (type === 'shorts') autoTitle = 'Kısa İçerik'
        else if (type === 'infographic') autoTitle = `${topic} — İnfografik`
        else if (type === 'motivation') autoTitle = `${topic} — Motivasyon`
        else autoTitle = `${lessonName} — ${topic}`
      }
      const job = await videoService.createJob({
        type,
        title: autoTitle,
        lesson_name: (type !== 'shorts' && type !== 'motivation' && type !== 'infographic')
          ? (lessonName.trim() || undefined) : undefined,
        topic: topic.trim() || undefined,
        description: description.trim() || undefined,
        format,
        target_duration_minutes: targetMinutes,
        infographic_template: type === 'infographic' ? infographicTemplate : undefined,
        questions: type === 'quiz' ? questions : undefined,
      })
      if (type === 'infographic') {
        toast.success('Görsel post oluşturuldu — incelemeye hazır!')
      } else {
        toast.success('Video üretim görevi başlatıldı!')
      }
      onCreated(job)
      onClose()
    } catch {
      toast.error('Görev oluşturulamadı')
    } finally {
      setLoading(false)
    }
  }

  // ── Adım 1: İçerik Seç ─────────────────────────────────────
  const renderContent = () => (
    <div style={{ padding: '24px 28px', display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Tip seçimi */}
      <div>
        <p style={{ fontSize: 13, fontWeight: 600, color: '#475569', margin: '0 0 10px' }}>Video Tipi</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {WIZARD_TYPES.map(({ type: t, label, desc }) => (
            <button key={t} onClick={() => handleTypeChange(t)} style={{
              textAlign: 'left', padding: '14px 18px', borderRadius: 12, cursor: 'pointer',
              border: `2px solid ${type === t ? '#0B2A4A' : '#e2e8f0'}`,
              background: type === t ? '#0B2A4A' : '#fff',
              transition: 'all 0.12s',
            }}>
              <p style={{ margin: 0, fontSize: 14, fontWeight: 700, color: type === t ? '#fff' : '#0B2A4A' }}>{label}</p>
              <p style={{ margin: '3px 0 0', fontSize: 12, color: type === t ? 'rgba(255,255,255,0.65)' : '#94a3b8' }}>{desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Ders + Konu (lesson/quiz) */}
      {type !== 'shorts' && type !== 'motivation' && type !== 'infographic' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
          <div>
            <label style={{ fontSize: 13, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 6 }}>
              Ders Adı <span style={{ color: '#ef4444' }}>*</span>
            </label>
            <input value={lessonName} onChange={e => setLessonName(e.target.value)}
              placeholder="Örn: Vergi Hukuku" style={INP} />
          </div>
          <div>
            <label style={{ fontSize: 13, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 6 }}>
              Konu <span style={{ color: '#ef4444' }}>*</span>
            </label>
            <input value={topic} onChange={e => setTopic(e.target.value)}
              placeholder="Örn: Katma Değer Vergisi" style={INP} />
          </div>
        </div>
      )}

      {/* Konu (shorts için opsiyonel) */}
      {type === 'shorts' && (
        <div>
          <label style={{ fontSize: 13, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 6 }}>
            Konu <span style={{ color: '#94a3b8', fontWeight: 400 }}>(opsiyonel)</span>
          </label>
          <input value={topic} onChange={e => setTopic(e.target.value)}
            placeholder="Örn: Vergi beyanname döneminde dikkat edilmesi gerekenler"
            style={INP} />
        </div>
      )}

      {/* Motivasyon — konu zorunlu */}
      {type === 'motivation' && (
        <div>
          <label style={{ fontSize: 13, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 6 }}>
            Motivasyon Konusu <span style={{ color: '#ef4444' }}>*</span>
          </label>
          <input value={topic} onChange={e => setTopic(e.target.value)}
            placeholder="Örn: SGS sınavına son hafta motivasyonu"
            style={INP} />
          <p style={{ margin: '6px 0 0', fontSize: 12, color: '#94a3b8' }}>
            15-30 saniye, dikey format (9:16), kinetik tipografi
          </p>
        </div>
      )}

      {/* İnfografik — konu + şablon seçimi */}
      {type === 'infographic' && (
        <>
          <div>
            <label style={{ fontSize: 13, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 6 }}>
              Konu <span style={{ color: '#ef4444' }}>*</span>
            </label>
            <input value={topic} onChange={e => setTopic(e.target.value)}
              placeholder="Örn: KDV hesaplama yöntemleri"
              style={INP} />
          </div>
          <div>
            <p style={{ fontSize: 13, fontWeight: 600, color: '#475569', margin: '0 0 10px' }}>Şablon Seçin</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {INFOGRAPHIC_TEMPLATES.map(({ value, label, desc }) => {
                const TemplateIcon = value === 'card_grid' ? LayoutGrid : value === 'comparison' ? ArrowLeftRight : ListOrdered
                return (
                  <button key={value} onClick={() => setInfographicTemplate(value)} style={{
                    textAlign: 'left', padding: '12px 16px', borderRadius: 10, cursor: 'pointer',
                    border: `2px solid ${infographicTemplate === value ? '#0B2A4A' : '#e2e8f0'}`,
                    background: infographicTemplate === value ? '#0B2A4A' : '#fff',
                    display: 'flex', alignItems: 'center', gap: 12,
                  }}>
                    <TemplateIcon size={18} color={infographicTemplate === value ? '#fff' : '#0B2A4A'} style={{ flexShrink: 0 }} />
                    <div>
                      <p style={{ margin: 0, fontSize: 13, fontWeight: 700, color: infographicTemplate === value ? '#fff' : '#0B2A4A' }}>{label}</p>
                      <p style={{ margin: '2px 0 0', fontSize: 12, color: infographicTemplate === value ? 'rgba(255,255,255,0.6)' : '#94a3b8' }}>{desc}</p>
                    </div>
                  </button>
                )
              })}
            </div>
            <p style={{ margin: '10px 0 0', fontSize: 12, color: '#0ea5e9', display: 'flex', alignItems: 'center', gap: 4 }}>
              <Zap size={11} /> Bilgi Merkezi&apos;ndeki belgelerden otomatik içerik çekilerek anında oluşturulur
            </p>
          </div>
        </>
      )}

      {/* Quiz sorular — katlanabilir */}
      {type === 'quiz' && (
        <div>
          <button
            onClick={() => setShowQuestions(v => !v)}
            style={{
              display: 'flex', alignItems: 'center', gap: 8,
              background: 'none', border: 'none', cursor: 'pointer', padding: 0,
              fontSize: 13, fontWeight: 600, color: '#475569',
            }}
          >
            <ChevronRight size={14} style={{ transition: 'transform 0.15s', transform: showQuestions ? 'rotate(90deg)' : 'none' }} />
            Soruları Manuel Gir
            <span style={{ fontWeight: 400, color: '#94a3b8' }}>(boş bırakırsanız GPT otomatik oluşturur)</span>
          </button>

          {showQuestions && (
            <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 12 }}>
              {questions?.map((q, qi) => (
                <div key={qi} style={{ border: '1.5px solid #e2e8f0', borderRadius: 12, padding: 16, background: '#fafafa' }}>
                  <p style={{ margin: '0 0 10px', fontSize: 13, fontWeight: 700, color: '#0B2A4A' }}>Soru {qi + 1}</p>
                  <textarea value={q.text} onChange={e => updateQuestion(qi, 'text', e.target.value)}
                    placeholder="Soru metni..." rows={2}
                    style={{ ...INP, resize: 'vertical', marginBottom: 8, fontSize: 13 }} />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 8 }}>
                    {q.options.map((opt, oi) => (
                      <div key={opt.label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span
                          onClick={() => updateQuestion(qi, 'correct_label', opt.label)}
                          style={{
                            width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
                            background: q.correct_label === opt.label ? '#10b981' : '#0B2A4A',
                            color: '#fff', fontSize: 12, fontWeight: 700,
                            display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
                          }}
                        >
                          {opt.label}
                        </span>
                        <input value={opt.text} onChange={e => updateOption(qi, oi, e.target.value)}
                          placeholder={`${opt.label} şıkkı`}
                          style={{
                            flex: 1, border: `1.5px solid ${q.correct_label === opt.label ? '#10b981' : '#e2e8f0'}`,
                            borderRadius: 8, padding: '7px 11px', fontSize: 13, outline: 'none', color: '#0f172a',
                          }} />
                      </div>
                    ))}
                  </div>
                  <input value={q.explanation ?? ''} onChange={e => updateQuestion(qi, 'explanation', e.target.value)}
                    placeholder="Doğru cevabın açıklaması (opsiyonel)" style={{ ...INP, fontSize: 12 }} />
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )

  // ── Adım 2: Format Seç ─────────────────────────────────────
  const renderFormat = () => (
    <div style={{ padding: '24px 28px', display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Format */}
      <div>
        <p style={{ fontSize: 13, fontWeight: 600, color: '#475569', margin: '0 0 10px' }}>Platform Formatı</p>
        <div style={{ display: 'flex', gap: 12 }}>
          {(['16:9', '9:16'] as VideoFormat[]).map(f => {
            const active = format === f
            return (
              <button key={f} onClick={() => setFormat(f)} style={{
                flex: 1, padding: '16px 12px', borderRadius: 12, cursor: 'pointer',
                border: `2px solid ${active ? '#0B2A4A' : '#e2e8f0'}`,
                background: active ? '#0B2A4A' : '#fff',
                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10,
              }}>
                {/* Oran görseli */}
                <div style={{
                  border: `2px solid ${active ? 'rgba(255,255,255,0.4)' : '#cbd5e1'}`,
                  borderRadius: 4,
                  width: f === '16:9' ? 64 : 36,
                  height: f === '16:9' ? 36 : 64,
                  background: active ? 'rgba(255,255,255,0.1)' : '#f8fafc',
                }} />
                <div>
                  <p style={{ margin: 0, fontSize: 13, fontWeight: 700, color: active ? '#fff' : '#0B2A4A' }}>
                    {f === '16:9' ? 'YouTube' : 'Reels / Shorts'}
                  </p>
                  <p style={{ margin: '2px 0 0', fontSize: 11, color: active ? 'rgba(255,255,255,0.6)' : '#94a3b8' }}>
                    {f} · {f === '16:9' ? 'Yatay' : 'Dikey'}
                  </p>
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Süre */}
      <div>
        <label style={{ fontSize: 13, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 6 }}>
          Hedef Süre (dakika)
        </label>
        <input type="number" min={1} max={60} value={targetMinutes}
          onChange={e => setTargetMinutes(Number(e.target.value))}
          style={{ ...INP, maxWidth: 140 }} />
        <p style={{ margin: '6px 0 0', fontSize: 12, color: '#94a3b8' }}>
          {format === '9:16' ? 'Kısa içerik için önerilen: 1 dakika' : type === 'quiz' ? 'Önerilen: 8–15 dakika' : 'Önerilen: 10–15 dakika'}
        </p>
      </div>

      {/* Gelişmiş ayarlar */}
      <div>
        <button
          onClick={() => setShowAdvanced(v => !v)}
          style={{
            display: 'flex', alignItems: 'center', gap: 8, background: 'none',
            border: 'none', cursor: 'pointer', padding: 0,
            fontSize: 13, fontWeight: 600, color: '#475569',
          }}
        >
          <ChevronRight size={14} style={{ transition: 'transform 0.15s', transform: showAdvanced ? 'rotate(90deg)' : 'none' }} />
          Gelişmiş Ayarlar
        </button>

        {showAdvanced && (
          <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 6 }}>
                Başlık <span style={{ color: '#94a3b8', fontWeight: 400 }}>(boş = otomatik)</span>
              </label>
              <input value={title} onChange={e => setTitle(e.target.value)}
                placeholder={type === 'quiz' ? 'Örn: SGS 2024 — KDV Soru Çözümü' : 'Örn: Vergi Hukuku — KDV Konu Anlatımı'}
                style={INP} />
            </div>
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 6 }}>
                Yönetmen Notu <span style={{ color: '#94a3b8', fontWeight: 400 }}>(opsiyonel)</span>
              </label>
              <textarea value={description} onChange={e => setDescription(e.target.value)}
                placeholder="Özel ton, vurgu noktası veya hedef kitle notu..."
                rows={3} style={{ ...INP, resize: 'vertical', lineHeight: 1.6 }} />
            </div>
          </div>
        )}
      </div>
    </div>
  )

  // ── Adım 3: Özet + Üret ───────────────────────────────────
  const renderReview = () => {
    let autoTitle = title.trim()
    if (!autoTitle) {
      if (type === 'shorts') autoTitle = 'Kısa İçerik'
      else if (type === 'infographic') autoTitle = `${topic} — İnfografik`
      else if (type === 'motivation') autoTitle = `${topic} — Motivasyon`
      else autoTitle = `${lessonName} — ${topic}`
    }
    const typeDef = WIZARD_TYPES.find(t => t.type === type)
    const templateDef = INFOGRAPHIC_TEMPLATES.find(t => t.value === infographicTemplate)
    const rows = [
      { label: 'Başlık', value: autoTitle },
      { label: 'Tip', value: typeDef?.label ?? type },
      ...(type !== 'shorts' && type !== 'motivation' && type !== 'infographic' ? [
        { label: 'Ders', value: lessonName },
        { label: 'Konu', value: topic },
      ] : []),
      ...(type === 'motivation' || type === 'infographic' ? [{ label: 'Konu', value: topic }] : []),
      ...(type === 'infographic' ? [{ label: 'Şablon', value: templateDef?.label ?? infographicTemplate }] : []),
      ...(type !== 'infographic' ? [
        { label: 'Platform', value: format === '16:9' ? 'YouTube (16:9 yatay)' : 'Reels / Shorts (9:16 dikey)' },
        { label: 'Hedef Süre', value: `${targetMinutes} dakika` },
      ] : [{ label: 'Format', value: '9:16 dikey — statik görsel' }]),
      ...(type === 'quiz' && showQuestions ? [{ label: 'Soru Girişi', value: 'Manuel (4 soru)' }] : []),
      ...(description.trim() ? [{ label: 'Not', value: description.trim() }] : []),
    ]
    return (
      <div style={{ padding: '24px 28px', display: 'flex', flexDirection: 'column', gap: 16 }}>
        <p style={{ margin: 0, fontSize: 13, color: '#64748b' }}>
          {type === 'infographic'
            ? 'Bilgi Merkezi verilerinizden otomatik infografik oluşturulacak. Onayladığınızda anında hazır olur.'
            : 'Aşağıdaki ayarlarla video üretimi başlatılacak. Onayladıktan sonra iş kuyruğa alınır.'}
        </p>
        <div style={{
          border: '1.5px solid #e2e8f0', borderRadius: 14, overflow: 'hidden',
        }}>
          {rows.map(({ label, value }, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'flex-start', gap: 16, padding: '12px 18px',
              background: i % 2 === 0 ? '#f8fafc' : '#fff',
              borderBottom: '1px solid #f1f5f9',
            }}>
              <span style={{ fontSize: 12, fontWeight: 600, color: '#94a3b8', width: 100, flexShrink: 0, paddingTop: 1, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                {label}
              </span>
              <span style={{ fontSize: 13, color: '#0f172a', fontWeight: 500 }}>{value}</span>
            </div>
          ))}
        </div>

        {/* Üretim süresi uyarısı — infographic'te gösterme */}
        {type !== 'infographic' && (
          <div style={{
            display: 'flex', alignItems: 'flex-start', gap: 10, padding: '12px 14px',
            background: '#fffbeb', border: '1.5px solid #fde68a', borderRadius: 10,
          }}>
            <AlertTriangle size={15} color="#d97706" style={{ flexShrink: 0, marginTop: 1 }} />
            <p style={{ margin: 0, fontSize: 12, color: '#92400e', lineHeight: 1.6 }}>
              Üretim süresi video uzunluğuna göre <strong>3–15 dakika</strong> sürebilir.
              Sayfadan ayrılabilirsiniz — iş arka planda devam eder ve tamamlandığında burada görünür.
            </p>
          </div>
        )}
        {type === 'infographic' && (
          <div style={{
            display: 'flex', alignItems: 'flex-start', gap: 10, padding: '12px 14px',
            background: '#f0f9ff', border: '1.5px solid #bae6fd', borderRadius: 10,
          }}>
            <Zap size={15} color="#0284c7" style={{ flexShrink: 0, marginTop: 1 }} />
            <p style={{ margin: 0, fontSize: 12, color: '#075985', lineHeight: 1.6 }}>
              Remotion render gerekmez — içerik anında oluşturulur ve incelemeye hazır olur.
            </p>
          </div>
        )}
      </div>
    )
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, padding: 24,
    }}>
      <div style={{
        background: '#fff', borderRadius: 20, width: '100%', maxWidth: 680,
        maxHeight: '92vh', overflow: 'hidden', display: 'flex', flexDirection: 'column',
        boxShadow: '0 24px 64px rgba(0,0,0,0.2)',
      }}>
        {/* Header */}
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '20px 28px 0', borderBottom: '1px solid #f1f5f9', paddingBottom: 16,
        }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#0B2A4A' }}>Yeni Video Görevi</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>
            <X size={20} />
          </button>
        </div>

        {/* Adım göstergesi */}
        <WizardIndicator step={step} />

        {/* İçerik */}
        <div style={{ overflow: 'auto', flex: 1 }}>
          {step === 'content' && renderContent()}
          {step === 'format'  && renderFormat()}
          {step === 'review'  && renderReview()}
        </div>

        {/* Footer */}
        <div style={{
          padding: '14px 28px', borderTop: '1px solid #f1f5f9',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12,
        }}>
          <div>
            {step !== 'content' && (
              <Button variant="secondary" onClick={() => setStep(step === 'review' ? 'format' : 'content')}>
                Geri
              </Button>
            )}
          </div>
          <div>
            {step === 'content' && (
              <Button onClick={() => {
                if (!validateContent()) return
                if (type === 'infographic') {
                  setFormat('9:16')
                  setTargetMinutes(1)
                  setStep('review')
                } else {
                  setStep('format')
                }
              }}>
                {type === 'infographic' ? <><Image size={14} /> Özeti Gör</> : <>Format Seç <ChevronRight size={15} /></>}
              </Button>
            )}
            {step === 'format' && (
              <Button onClick={() => setStep('review')}>
                Özeti Gör <ChevronRight size={15} />
              </Button>
            )}
            {step === 'review' && (
              <Button onClick={handleSubmit} disabled={loading}>
                {loading
                  ? <><Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> Başlatılıyor...</>
                  : type === 'infographic'
                    ? <><Image size={14} /> Görsel Post Oluştur</>
                    : <><Film size={14} /> Video Görevi Başlat</>}
              </Button>
            )}
          </div>
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
  const [pollTimedOut, setPollTimedOut] = useState(false)
  const [circuitOpen, setCircuitOpen] = useState(false)
  const [circuitInfo, setCircuitInfo] = useState<{ consecutive_failures: number; threshold: number } | null>(null)
  const [resettingCircuit, setResettingCircuit] = useState(false)
  const pollRef = useRef<NodeJS.Timeout | null>(null)
  const pollStartRef = useRef<number>(0)
  const jobsRef = useRef<VideoJob[]>([]) // closure-safe ref
  const POLL_MAX_MS = 20 * 60 * 1000 // 20 dakika

  const ACTIVE_STATUSES = ['scripting', 'tts_generating', 'warmup_pinging', 'rendering']

  const loadJobs = async () => {
    try {
      const data = await videoService.listJobs(filter === 'all' ? undefined : filter)
      setJobs(data)
      jobsRef.current = data
    } catch {
      // sessiz
    } finally {
      setLoading(false)
    }
  }

  const checkCircuit = async () => {
    try {
      const health = await videoService.renderHealth()
      setCircuitOpen(health.circuit_open)
      setCircuitInfo({ consecutive_failures: health.consecutive_failures, threshold: health.threshold })
    } catch {
      // render health endpoint yoksa sessizce geç
    }
  }

  const handleResetCircuit = async () => {
    setResettingCircuit(true)
    try {
      await videoService.resetCircuit()
      setCircuitOpen(false)
      setCircuitInfo(null)
      toast.success('Render devresi sıfırlandı — yeni iş başlatabilirsiniz')
    } catch {
      toast.error('Devre sıfırlanamadı')
    } finally {
      setResettingCircuit(false)
    }
  }

  useEffect(() => {
    checkCircuit()
    loadJobs()
    setPollTimedOut(false)
    pollStartRef.current = Date.now()

    pollRef.current = setInterval(async () => {
      // jobsRef her zaman güncel — closure bug yok
      const hasActive = jobsRef.current.some(j => ACTIVE_STATUSES.includes(j.status))
      if (!hasActive) return

      if (Date.now() - pollStartRef.current > POLL_MAX_MS) {
        if (pollRef.current) clearInterval(pollRef.current)
        setPollTimedOut(true)
        return
      }

      try {
        const data = await videoService.listJobs(filter === 'all' ? undefined : filter)
        setJobs(data)
        jobsRef.current = data
        const stillActive = data.some(j => ACTIVE_STATUSES.includes(j.status))
        if (!stillActive && pollRef.current) clearInterval(pollRef.current)
      } catch { /* sessiz */ }
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

  const handleRegenerate = async (job: VideoJob, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await videoService.regenerateJob(job.id)
      toast.success('Yeniden üretim başlatıldı')
      loadJobs()
    } catch { toast.error('Yeniden üretim başlatılamadı') }
  }

  const pendingReview = jobs.filter(j => j.status === 'ready_for_review')
  const activeJobs = jobs.filter(j => ['scripting', 'tts_generating', 'warmup_pinging', 'rendering'].includes(j.status))

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

        {/* Circuit breaker uyarısı */}
        {circuitOpen && (
          <div style={{
            marginBottom: 16, padding: '12px 16px', borderRadius: 12,
            background: '#fff1f2', border: '1.5px solid #fca5a5',
            display: 'flex', alignItems: 'center', gap: 10,
          }}>
            <XCircle size={16} color="#ef4444" style={{ flexShrink: 0 }} />
            <div style={{ flex: 1 }}>
              <p style={{ margin: 0, fontSize: 13, fontWeight: 700, color: '#b91c1c' }}>
                Render devresi açık — yeni video işleri başlatılamaz
              </p>
              {circuitInfo && (
                <p style={{ margin: '2px 0 0', fontSize: 12, color: '#ef4444' }}>
                  {circuitInfo.consecutive_failures}/{circuitInfo.threshold} ardışık hata. Railway render servisini kontrol edin.
                </p>
              )}
            </div>
            <button
              onClick={handleResetCircuit}
              disabled={resettingCircuit}
              style={{
                padding: '5px 14px', borderRadius: 8, flexShrink: 0,
                border: '1.5px solid #ef4444', background: '#fff',
                color: '#ef4444', fontSize: 12, fontWeight: 700, cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 6,
                opacity: resettingCircuit ? 0.6 : 1,
              }}
            >
              {resettingCircuit
                ? <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} />
                : <RefreshCw size={12} />}
              Devreyi Sıfırla
            </button>
          </div>
        )}

        {/* Polling zaman aşımı uyarısı */}
        {pollTimedOut && (
          <div style={{
            marginBottom: 16, padding: '12px 16px', borderRadius: 12,
            background: '#fff7ed', border: '1.5px solid #fed7aa',
            display: 'flex', alignItems: 'center', gap: 10,
          }}>
            <AlertTriangle size={16} color="#ea580c" />
            <p style={{ margin: 0, fontSize: 13, color: '#9a3412' }}>
              20 dakika geçti — durum alınamıyor. Sayfayı yenileyerek güncel durumu görün.
            </p>
            <button
              onClick={() => { setPollTimedOut(false); loadJobs(); pollStartRef.current = Date.now() }}
              style={{
                marginLeft: 'auto', padding: '4px 12px', borderRadius: 8,
                border: '1.5px solid #ea580c', background: 'transparent',
                color: '#ea580c', fontSize: 12, fontWeight: 600, cursor: 'pointer',
              }}
            >
              Yenile
            </button>
          </div>
        )}

        {/* Filtreler */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
          {(['all', 'quiz', 'lesson', 'shorts', 'motivation', 'infographic'] as const).map(f => (
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
                  background: job.status === 'failed' ? '#fff5f5' : '#fff',
                  border: `1.5px solid ${job.status === 'failed' ? '#fca5a5' : job.status === 'ready_for_review' ? '#ddd6fe' : '#e2e8f0'}`,
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
                  background: job.status === 'failed' ? '#fee2e2' : job.type === 'infographic' ? '#f0f9ff' : '#f1f5f9',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {job.type === 'infographic'
                    ? <Image size={22} color={job.status === 'failed' ? '#ef4444' : '#0284c7'} />
                    : <Film size={22} color={job.status === 'failed' ? '#ef4444' : '#0B2A4A'} />}
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
                  {ACTIVE_STATUSES.includes(job.status) && (
                    <>
                      <PipelineBar status={job.status} />
                      {job.status === 'warmup_pinging' && (
                        <p style={{ margin: '4px 0 0', fontSize: 12, color: '#0ea5e9' }}>
                          Render servisi uyanıyor — ~60 sn
                        </p>
                      )}
                    </>
                  )}
                  {job.error_message && (
                    <p style={{ margin: '6px 0 0', fontSize: 12, color: '#ef4444' }}>
                      {job.error_message}
                    </p>
                  )}
                  {job.status === 'failed' && (
                    <button
                      onClick={e => handleRegenerate(job, e)}
                      style={{
                        marginTop: 10, padding: '5px 14px', borderRadius: 8,
                        border: '1.5px solid #ef4444', background: '#fff',
                        color: '#ef4444', fontSize: 12, fontWeight: 700, cursor: 'pointer',
                      }}
                    >
                      Yeniden Dene
                    </button>
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
