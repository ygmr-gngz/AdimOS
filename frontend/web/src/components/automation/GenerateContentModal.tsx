'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Modal from '@/components/ui/Modal'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import type { ContentPlatform, ContentType, GenerateContentRequest } from '@/types/automation'

interface GenerateContentModalProps {
  isOpen: boolean
  onClose: () => void
  onGenerate: (request: GenerateContentRequest) => Promise<void>
}

type ContentOption = {
  platform: ContentPlatform
  content_type: ContentType
  backend_type: string
  label: string
  description: string
  showQuestion?: boolean
}

const CONTENT_OPTIONS: ContentOption[] = [
  {
    platform: 'youtube_shorts',
    content_type: 'short',
    backend_type: 'short',
    label: 'YouTube Shorts',
    description: '45-60 sn — danışan çeken, merak uyandıran kısa video',
  },
  {
    platform: 'instagram',
    content_type: 'reel',
    backend_type: 'short',
    label: 'Instagram Reel',
    description: '45-60 sn dikey video — bilgilendirici, hızlı tempo',
  },
  {
    platform: 'instagram',
    content_type: 'post',
    backend_type: 'post',
    label: 'Instagram Görsel Post',
    description: 'Bilgilendirici infografik / tablo formatı görsel',
  },
]

const BACKEND_ROUTE: Record<string, string> = {
  short: 'short',
  post: 'post',
}

type Category = 'smmm' | 'sgs' | 'genel'

const CATEGORY_OPTIONS: { value: Category; label: string; desc: string }[] = [
  { value: 'smmm',  label: 'SMMM / YMM', desc: 'Muhasebe, vergi, SGK, ticaret hukuku' },
  { value: 'sgs',   label: 'SGS',         desc: 'SGS sınavı — ders bazlı soru çözümü' },
  { value: 'genel', label: 'Genel',       desc: 'Muhasebe, vergi, girişimcilik' },
]

const SGS_LESSONS = [
  'Türkçe',
  'Matematik',
  'Tarih-Genel Kültür',
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
]

export default function GenerateContentModal({ isOpen, onClose, onGenerate }: GenerateContentModalProps) {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [topic, setTopic] = useState('')
  const [questionText, setQuestionText] = useState('')
  const [selectedIdx, setSelectedIdx] = useState(0)
  const [category, setCategory] = useState<Category>('smmm')
  const [sgsLesson, setSgsLesson] = useState('')

  const selected = CONTENT_OPTIONS[selectedIdx]
  const isSgs = category === 'sgs'

  const handleSubmit = async () => {
    if (!topic.trim()) return
    if (isSgs && !sgsLesson) return
    setIsLoading(true)
    try {
      const finalTopic = isSgs && sgsLesson
        ? `[${sgsLesson}] ${topic.trim()}`
        : topic.trim()

      await onGenerate({
        topic: finalTopic,
        platform: selected.platform,
        content_type: selected.content_type,
        backend_type: BACKEND_ROUTE[selected.backend_type],
        question_text: questionText.trim() || undefined,
        category,
      })
      onClose()
      setTopic('')
      setQuestionText('')
      setSgsLesson('')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Yeni İçerik Üret" size="lg">
      <div className="space-y-4">

        {/* Video yönlendirmesi */}
        <div className="flex items-center justify-between bg-blue-500/10 border border-blue-500/30 rounded-xl px-4 py-3">
          <p className="text-xs text-blue-300">
            Konu anlatım ve soru çözüm <strong>videoları</strong> Video Prodüksiyon&apos;da üretilir.
          </p>
          <button
            onClick={() => { onClose(); router.push('/video') }}
            className="ml-3 shrink-0 text-xs font-semibold text-blue-400 hover:text-blue-200 underline underline-offset-2 transition-colors"
          >
            Git →
          </button>
        </div>

        {/* İçerik tipi seçimi */}
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-2">İçerik Türü</label>
          <div className="grid grid-cols-1 gap-2">
            {CONTENT_OPTIONS.map((opt, i) => (
              <button
                key={i}
                onClick={() => setSelectedIdx(i)}
                className={`text-left px-4 py-3 rounded-xl border transition-colors ${
                  selectedIdx === i
                    ? 'bg-brand-600/20 border-brand-500/50 text-gray-100'
                    : 'bg-surface-100 border-surface-200 text-gray-400 hover:border-surface-300 hover:text-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${
                    opt.platform === 'youtube' || opt.platform === 'youtube_shorts'
                      ? 'bg-red-500/20 text-red-400'
                      : 'bg-pink-500/20 text-pink-400'
                  }`}>
                    {opt.platform === 'youtube' || opt.platform === 'youtube_shorts' ? 'YT' : 'IG'}
                  </span>
                  <span className="text-sm font-medium">{opt.label}</span>
                </div>
                <p className="text-xs text-gray-600 mt-0.5 ml-8">{opt.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Kategori */}
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-2">Kategori</label>
          <div className="flex gap-2">
            {CATEGORY_OPTIONS.map((cat) => (
              <button
                key={cat.value}
                onClick={() => { setCategory(cat.value); setSgsLesson('') }}
                className={`flex-1 text-center px-3 py-2 rounded-xl border text-xs transition-colors ${
                  category === cat.value
                    ? 'bg-brand-600/20 border-brand-500/50 text-gray-100 font-semibold'
                    : 'bg-surface-100 border-surface-200 text-gray-500 hover:border-surface-300 hover:text-gray-300'
                }`}
              >
                <div>{cat.label}</div>
                <div className="text-gray-600 text-[10px] mt-0.5">{cat.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* SGS Ders Seçimi */}
        {isSgs && (
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-2">
              Ders <span className="text-red-400">*</span>
            </label>
            <div className="grid grid-cols-2 gap-1.5 max-h-48 overflow-y-auto pr-1">
              {SGS_LESSONS.map((lesson) => (
                <button
                  key={lesson}
                  type="button"
                  onClick={() => setSgsLesson(lesson)}
                  className={`text-left px-3 py-2 rounded-lg border text-xs transition-colors ${
                    sgsLesson === lesson
                      ? 'bg-brand-600/30 border-brand-500/60 text-brand-300 font-medium'
                      : 'bg-surface-100 border-surface-200 text-gray-500 hover:border-surface-300 hover:text-gray-300'
                  }`}
                >
                  {lesson}
                </button>
              ))}
            </div>
            {!sgsLesson && (
              <p className="text-xs text-amber-500/80 mt-1.5">Ders seçilmeden devam edilemez</p>
            )}
          </div>
        )}

        {/* Konu */}
        <Input
          label="Konu"
          placeholder={
            isSgs
              ? sgsLesson
                ? `Ör: ${sgsLesson} — 2023 sınav sorusu çözümü`
                : 'Önce ders seçin...'
              : selected.backend_type === 'question_solution'
              ? 'Ör: Ticaret Hukuku — İşletme Adı'
              : selected.backend_type === 'topic_explanation'
              ? 'Ör: KDV Beyannamesi Nasıl Hazırlanır'
              : 'Ör: Yeni girişimcinin bilmesi gereken 3 vergi'
          }
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          disabled={isSgs && !sgsLesson}
        />

        {/* Soru metni (sadece soru çözümde göster) */}
        {selected.showQuestion && (
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">
              Soru Metni <span className="text-gray-600">(opsiyonel — boş bırakırsanız AI üretir)</span>
            </label>
            <textarea
              value={questionText}
              onChange={(e) => setQuestionText(e.target.value)}
              rows={3}
              placeholder="Sınav sorusunu buraya yapıştırın veya boş bırakın..."
              className="w-full bg-surface-100 border border-surface-200 rounded-xl px-3 py-2.5 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
            />
          </div>
        )}

        <div className="flex gap-3 pt-1">
          <Button variant="secondary" onClick={onClose} className="flex-1">İptal</Button>
          <Button
            onClick={handleSubmit}
            isLoading={isLoading}
            disabled={!topic.trim() || (isSgs && !sgsLesson)}
            className="flex-1"
          >
            Üretimi Başlat
          </Button>
        </div>
      </div>
    </Modal>
  )
}
