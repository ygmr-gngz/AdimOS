'use client'

import { useState } from 'react'
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
    platform: 'youtube',
    content_type: 'video',
    backend_type: 'topic_explanation',
    label: 'Konu Anlatım Videosu',
    description: 'Muhasebe, vergi, SGK, ticaret hukuku konu anlatımı (5-10 dk)',
  },
  {
    platform: 'youtube',
    content_type: 'video',
    backend_type: 'question_solution',
    label: 'Soru Çözüm Videosu',
    description: 'SMMM/YMM sınav sorusu çözüm formatı — soru, şıklar, açıklama',
    showQuestion: true,
  },
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
  topic_explanation: 'topic-explanation',
  question_solution: 'question-solution',
  short: 'short',
  post: 'post',
  video: 'video',
}

const CATEGORY_OPTIONS = [
  { value: 'smmm', label: 'SMMM / YMM', desc: 'Muhasebe, vergi, SGK, ticaret hukuku' },
  { value: 'sgs',  label: 'SGS', desc: 'SGS mevzuatı, iş hukuku, SGS prosedürleri' },
  { value: 'genel', label: 'Genel', desc: 'Muhasebe, vergi, girişimcilik' },
]

export default function GenerateContentModal({ isOpen, onClose, onGenerate }: GenerateContentModalProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [topic, setTopic] = useState('')
  const [questionText, setQuestionText] = useState('')
  const [selectedIdx, setSelectedIdx] = useState(0)
  const [category, setCategory] = useState('smmm')

  const selected = CONTENT_OPTIONS[selectedIdx]

  const handleSubmit = async () => {
    if (!topic.trim()) return
    setIsLoading(true)
    try {
      await onGenerate({
        topic: topic.trim(),
        platform: selected.platform,
        content_type: selected.content_type,
        backend_type: BACKEND_ROUTE[selected.backend_type],
        question_text: questionText.trim() || undefined,
        category,
      })
      onClose()
      setTopic('')
      setQuestionText('')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Yeni İçerik Üret" size="lg">
      <div className="space-y-4">

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
                onClick={() => setCategory(cat.value)}
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

        {/* Konu */}
        <Input
          label="Konu"
          placeholder={
            selected.backend_type === 'question_solution'
              ? 'Ör: Ticaret Hukuku — İşletme Adı'
              : selected.backend_type === 'topic_explanation'
              ? 'Ör: KDV Beyannamesi Nasıl Hazırlanır'
              : 'Ör: Yeni girişimcinin bilmesi gereken 3 vergi'
          }
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
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
          <Button onClick={handleSubmit} isLoading={isLoading} disabled={!topic.trim()} className="flex-1">
            Üretimi Başlat
          </Button>
        </div>
      </div>
    </Modal>
  )
}
