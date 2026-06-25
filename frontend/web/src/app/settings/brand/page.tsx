'use client'

import { useEffect, useRef, useState } from 'react'
import AppShell from '@/components/layout/AppShell'
import Button from '@/components/ui/Button'
import { Upload, Trash2, CheckCircle, Info } from 'lucide-react'
import { brandService, type BrandSettings } from '@/services/brand.service'
import toast from 'react-hot-toast'

const VIDEO_TYPE_INFO = [
  { label: 'SGS Soru/Konu Videosu', style: 'Merkez filigran · %7 opaklık · Büyük alan' },
  { label: 'Motivasyon Reels/Shorts', style: 'Sağ üst köşe · Görünür · Küçük' },
  { label: 'Genel Eğitim Videosu', style: 'Merkez filigran · %6 opaklık' },
  { label: 'Post / Görsel İçerik', style: 'Sağ alt köşe · Görünür · Küçük' },
]

export default function BrandSettingsPage() {
  const [settings, setSettings] = useState<BrandSettings | null>(null)
  const [uploading, setUploading] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    brandService.getSettings().then(setSettings).catch(() => {})
  }, [])

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const result = await brandService.uploadLogo(file)
      setSettings(prev => prev ? { ...prev, logo_url: result.logo_url, watermark_enabled: true } : null)
      toast.success('Logo yüklendi — tüm yeni videolara otomatik eklenecek')
    } catch {
      toast.error('Logo yüklenemedi. Dosya boyutunu ve formatını kontrol et (PNG/JPG/WebP, maks 5 MB)')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const handleDeleteLogo = async () => {
    try {
      await brandService.deleteLogo()
      setSettings(prev => prev ? { ...prev, logo_url: undefined } : null)
      toast.success('Logo kaldırıldı')
    } catch {
      toast.error('Silinemedi')
    }
  }

  const handleToggle = async () => {
    if (!settings) return
    const newVal = !settings.watermark_enabled
    try {
      await brandService.updateSettings({ watermark_enabled: newVal })
      setSettings(prev => prev ? { ...prev, watermark_enabled: newVal } : null)
      toast.success(newVal ? 'Filigran aktif edildi' : 'Filigran devre dışı')
    } catch {
      toast.error('Ayar kaydedilemedi')
    }
  }

  return (
    <AppShell>
      <div className="max-w-xl space-y-6 animate-fade-in">
        <div>
          <h2 className="text-xl font-bold text-white">Marka Ayarları</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            Logoyu bir kez yükle — sistem video türüne göre otomatik yerleştirir
          </p>
        </div>

        {/* Logo */}
        <div className="bg-surface-50 rounded-xl border border-surface-200 p-5 space-y-4">
          <h3 className="text-sm font-semibold text-gray-300">Adım Müşavir Logosu</h3>

          {settings?.logo_url ? (
            <div className="flex items-center gap-4">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={settings.logo_url}
                alt="Logo"
                className="h-16 w-auto object-contain rounded-lg bg-white/5 p-2 border border-surface-200"
              />
              <div className="flex-1 space-y-2">
                <div className="flex items-center gap-1.5 text-xs text-green-400">
                  <CheckCircle size={12} /> Logo yüklü — videolara eklenecek
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => fileRef.current?.click()}
                    className="text-xs text-gray-400 hover:text-gray-200 underline"
                  >
                    Değiştir
                  </button>
                  <span className="text-gray-700">·</span>
                  <button
                    onClick={handleDeleteLogo}
                    className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300"
                  >
                    <Trash2 size={10} /> Kaldır
                  </button>
                </div>
              </div>
              <button
                onClick={handleToggle}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                  settings.watermark_enabled
                    ? 'bg-brand-600/20 border-brand-500/50 text-brand-300'
                    : 'bg-surface-100 border-surface-200 text-gray-500'
                }`}
              >
                {settings.watermark_enabled ? 'Filigran Açık' : 'Filigran Kapalı'}
              </button>
            </div>
          ) : (
            <div
              onClick={() => fileRef.current?.click()}
              className="flex flex-col items-center justify-center gap-3 border-2 border-dashed border-surface-300 rounded-xl py-12 cursor-pointer hover:border-brand-500/50 transition-colors"
            >
              <Upload size={22} className="text-gray-600" />
              <div className="text-center">
                <p className="text-sm text-gray-400 font-medium">Logo yükle</p>
                <p className="text-xs text-gray-600 mt-0.5">PNG, JPG veya WebP · maks 5 MB</p>
              </div>
              <Button size="sm" isLoading={uploading}>Logo Seç</Button>
            </div>
          )}

          <input
            ref={fileRef}
            type="file"
            accept=".png,.jpg,.jpeg,.webp"
            className="hidden"
            onChange={handleLogoUpload}
          />
        </div>

        {/* Otomatik yerleşim bilgisi */}
        <div className="bg-surface-50 rounded-xl border border-surface-200 p-5 space-y-3">
          <div className="flex items-center gap-2">
            <Info size={13} className="text-brand-400" />
            <h3 className="text-sm font-semibold text-gray-300">Otomatik Yerleşim</h3>
          </div>
          <p className="text-xs text-gray-500">
            Manuel ayar yok — sistem içerik türüne göre logoyu doğru şekilde ekler:
          </p>
          <div className="space-y-2">
            {VIDEO_TYPE_INFO.map(({ label, style }) => (
              <div key={label} className="flex items-start gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-brand-500 mt-1.5 shrink-0" />
                <div>
                  <p className="text-xs font-medium text-gray-300">{label}</p>
                  <p className="text-xs text-gray-600">{style}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  )
}
