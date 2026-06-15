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

const PLATFORMS: ContentPlatform[] = ['instagram', 'youtube', 'youtube_shorts', 'tiktok']

const PLATFORM_LABEL: Record<ContentPlatform, string> = {
  instagram: 'Instagram',
  youtube: 'YouTube',
  youtube_shorts: 'YouTube Shorts',
  tiktok: 'TikTok',
}

const CONTENT_TYPES: Record<ContentPlatform, ContentType[]> = {
  instagram: ['reel', 'post', 'story'],
  youtube: ['video'],
  youtube_shorts: ['short'],
  tiktok: ['video'],
}

type Tone = NonNullable<GenerateContentRequest['tone']>

const TONES: { value: Tone; label: string }[] = [
  { value: 'professional', label: 'Profesyonel' },
  { value: 'casual', label: 'Samimi' },
  { value: 'educational', label: 'Eğitici' },
  { value: 'promotional', label: 'Tanıtım' },
]

export default function GenerateContentModal({ isOpen, onClose, onGenerate }: GenerateContentModalProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [topic, setTopic] = useState('')
  const [platform, setPlatform] = useState<ContentPlatform>('instagram')
  const [contentType, setContentType] = useState<ContentType>('reel')
  const [tone, setTone] = useState<Tone>('professional')
  const [targetAudience, setTargetAudience] = useState('')
  const [keywordsInput, setKeywordsInput] = useState('')

  const handlePlatformChange = (value: string) => {
    const p = value as ContentPlatform
    setPlatform(p)
    setContentType(CONTENT_TYPES[p][0])
  }

  const handleSubmit = async () => {
    if (!topic.trim()) return
    setIsLoading(true)
    try {
      await onGenerate({
        topic: topic.trim(),
        platform,
        content_type: contentType,
        tone,
        target_audience: targetAudience || undefined,
        keywords: keywordsInput.split(',').map((k) => k.trim()).filter(Boolean),
      })
      onClose()
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Yeni İçerik Üret" size="md">
      <div className="space-y-4">
        <Input
          label="Konu"
          placeholder="Ör: SGS sınavına hazırlık ipuçları"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
        />

        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-300">Platform</label>
            <select
              value={platform}
              onChange={(e) => handlePlatformChange(e.target.value)}
              className="bg-surface-100 border border-surface-200 rounded-lg px-3 py-2.5 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              {PLATFORMS.map((p) => (
                <option key={p} value={p}>{PLATFORM_LABEL[p]}</option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-300">İçerik Tipi</label>
            <select
              value={contentType}
              onChange={(e) => setContentType(e.target.value as ContentType)}
              className="bg-surface-100 border border-surface-200 rounded-lg px-3 py-2.5 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              {CONTENT_TYPES[platform].map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-gray-300">Ton</label>
          <select
            value={tone}
            onChange={(e) => setTone(e.target.value as Tone)}
            className="bg-surface-100 border border-surface-200 rounded-lg px-3 py-2.5 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            {TONES.map(({ value, label }) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </div>

        <Input
          label="Hedef Kitle (opsiyonel)"
          placeholder="Ör: SGS sınavına girecek adaylar"
          value={targetAudience}
          onChange={(e) => setTargetAudience(e.target.value)}
        />

        <Input
          label="Anahtar Kelimeler (virgülle ayırın)"
          placeholder="Ör: sgs, işkur, kariyer"
          value={keywordsInput}
          onChange={(e) => setKeywordsInput(e.target.value)}
        />

        <div className="flex gap-3 pt-2">
          <Button variant="secondary" onClick={onClose} className="flex-1">
            İptal
          </Button>
          <Button
            onClick={handleSubmit}
            isLoading={isLoading}
            disabled={!topic.trim()}
            className="flex-1"
          >
            İçerik Üret
          </Button>
        </div>
      </div>
    </Modal>
  )
}
