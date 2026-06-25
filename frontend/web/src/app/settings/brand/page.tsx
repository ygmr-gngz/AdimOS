'use client'

import { useEffect, useRef, useState } from 'react'
import AppShell from '@/components/layout/AppShell'
import Button from '@/components/ui/Button'
import { Upload, Trash2, Image as ImageIcon, Eye, EyeOff } from 'lucide-react'
import { brandService, POSITION_LABELS, type BrandSettings } from '@/services/brand.service'
import toast from 'react-hot-toast'

const DEFAULT_SETTINGS: BrandSettings = {
  watermark_enabled: true,
  watermark_opacity: 0.07,
  watermark_position: 'center',
  watermark_size: 0.30,
  logo_corner_position: 'top-right',
}

const POSITIONS = ['center', 'top-right', 'top-left', 'bottom-right', 'bottom-left'] as const

export default function BrandSettingsPage() {
  const [settings, setSettings] = useState<BrandSettings>(DEFAULT_SETTINGS)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    brandService.getSettings()
      .then(s => setSettings({ ...DEFAULT_SETTINGS, ...s }))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const handleSave = async () => {
    setSaving(true)
    try {
      const updated = await brandService.updateSettings({
        watermark_enabled: settings.watermark_enabled,
        watermark_opacity: settings.watermark_opacity,
        watermark_position: settings.watermark_position,
        watermark_size: settings.watermark_size,
        logo_corner_position: settings.logo_corner_position,
      })
      setSettings(prev => ({ ...prev, ...updated }))
      toast.success('Marka ayarları kaydedildi')
    } catch {
      toast.error('Kaydedilemedi')
    } finally {
      setSaving(false)
    }
  }

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const result = await brandService.uploadLogo(file)
      setSettings(prev => ({ ...prev, logo_url: result.logo_url }))
      toast.success('Logo yüklendi')
    } catch {
      toast.error('Logo yüklenemedi')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const handleDeleteLogo = async () => {
    try {
      await brandService.deleteLogo()
      setSettings(prev => ({ ...prev, logo_url: null }))
      toast.success('Logo kaldırıldı')
    } catch {
      toast.error('Silinemedi')
    }
  }

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-64 text-gray-500">Yükleniyor…</div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className="max-w-2xl space-y-6 animate-fade-in">
        <div>
          <h2 className="text-xl font-bold text-white">Marka Ayarları</h2>
          <p className="text-sm text-gray-500 mt-0.5">Logo ve filigran ayarları tüm videolara uygulanır</p>
        </div>

        {/* Logo yükleme */}
        <div className="bg-surface-50 rounded-xl border border-surface-200 p-5 space-y-4">
          <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
            <ImageIcon size={14} className="text-brand-400" /> Adım Müşavir Logosu
          </h3>

          {settings.logo_url ? (
            <div className="flex items-center gap-4">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={settings.logo_url}
                alt="Logo"
                className="h-16 w-auto object-contain rounded-lg bg-white/5 p-2"
              />
              <div className="flex-1">
                <p className="text-xs text-gray-400 truncate">{settings.logo_url.split('/').pop()}</p>
                <button
                  onClick={handleDeleteLogo}
                  className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300 mt-1"
                >
                  <Trash2 size={11} /> Logoyu kaldır
                </button>
              </div>
            </div>
          ) : (
            <div
              onClick={() => fileRef.current?.click()}
              className="flex flex-col items-center justify-center gap-2 border-2 border-dashed border-surface-300 rounded-xl py-10 cursor-pointer hover:border-brand-500/50 transition-colors"
            >
              <Upload size={20} className="text-gray-600" />
              <p className="text-sm text-gray-500">PNG, JPG veya SVG — maks 5 MB</p>
              <Button size="sm" isLoading={uploading}>Logo Yükle</Button>
            </div>
          )}

          <input
            ref={fileRef}
            type="file"
            accept=".png,.jpg,.jpeg,.svg,.webp"
            className="hidden"
            onChange={handleLogoUpload}
          />

          {settings.logo_url && (
            <Button size="sm" variant="ghost" onClick={() => fileRef.current?.click()} isLoading={uploading}>
              <Upload size={12} /> Logoyu değiştir
            </Button>
          )}
        </div>

        {/* Filigran ayarları */}
        <div className="bg-surface-50 rounded-xl border border-surface-200 p-5 space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-300">Filigran Ayarları</h3>
            <button
              onClick={() => setSettings(prev => ({ ...prev, watermark_enabled: !prev.watermark_enabled }))}
              className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                settings.watermark_enabled
                  ? 'bg-brand-600/20 border-brand-500/50 text-brand-300'
                  : 'bg-surface-100 border-surface-200 text-gray-500'
              }`}
            >
              {settings.watermark_enabled ? <Eye size={12} /> : <EyeOff size={12} />}
              {settings.watermark_enabled ? 'Aktif' : 'Pasif'}
            </button>
          </div>

          <div className={`space-y-4 ${!settings.watermark_enabled ? 'opacity-40 pointer-events-none' : ''}`}>
            {/* Konum */}
            <div>
              <label className="text-xs font-medium text-gray-400 mb-2 block">Filigran Konumu</label>
              <div className="grid grid-cols-5 gap-1.5">
                {POSITIONS.map(pos => (
                  <button
                    key={pos}
                    onClick={() => setSettings(prev => ({ ...prev, watermark_position: pos }))}
                    className={`text-xs px-2 py-2 rounded-lg border transition-colors text-center ${
                      settings.watermark_position === pos
                        ? 'bg-brand-600/20 border-brand-500/50 text-brand-300'
                        : 'bg-surface-100 border-surface-200 text-gray-500 hover:text-gray-300'
                    }`}
                  >
                    {POSITION_LABELS[pos]?.replace(' filigran', '') || pos}
                  </button>
                ))}
              </div>
            </div>

            {/* Opacity */}
            <div>
              <div className="flex justify-between mb-1">
                <label className="text-xs font-medium text-gray-400">Opaklık</label>
                <span className="text-xs text-gray-500">%{Math.round(settings.watermark_opacity * 100)}</span>
              </div>
              <input
                type="range"
                min="1" max="30" step="1"
                value={Math.round(settings.watermark_opacity * 100)}
                onChange={e => setSettings(prev => ({ ...prev, watermark_opacity: Number(e.target.value) / 100 }))}
                className="w-full accent-brand-500"
              />
              <div className="flex justify-between text-xs text-gray-700 mt-0.5">
                <span>%1 (çok silik)</span><span>%30 (görünür)</span>
              </div>
            </div>

            {/* Boyut */}
            <div>
              <div className="flex justify-between mb-1">
                <label className="text-xs font-medium text-gray-400">Boyut</label>
                <span className="text-xs text-gray-500">%{Math.round(settings.watermark_size * 100)}</span>
              </div>
              <input
                type="range"
                min="5" max="60" step="5"
                value={Math.round(settings.watermark_size * 100)}
                onChange={e => setSettings(prev => ({ ...prev, watermark_size: Number(e.target.value) / 100 }))}
                className="w-full accent-brand-500"
              />
              <div className="flex justify-between text-xs text-gray-700 mt-0.5">
                <span>%5 (küçük)</span><span>%60 (büyük)</span>
              </div>
            </div>

            {/* Köşe logosu */}
            <div>
              <label className="text-xs font-medium text-gray-400 mb-2 block">
                Köşe Logosu (filigran yerine)
              </label>
              <div className="grid grid-cols-4 gap-1.5">
                {(['top-right', 'top-left', 'bottom-right', 'bottom-left'] as const).map(pos => (
                  <button
                    key={pos}
                    onClick={() => setSettings(prev => ({ ...prev, logo_corner_position: pos }))}
                    className={`text-xs px-2 py-2 rounded-lg border transition-colors ${
                      settings.logo_corner_position === pos
                        ? 'bg-brand-600/20 border-brand-500/50 text-brand-300'
                        : 'bg-surface-100 border-surface-200 text-gray-500 hover:text-gray-300'
                    }`}
                  >
                    {POSITION_LABELS[pos]}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Kaydet */}
        <div className="flex justify-end">
          <Button onClick={handleSave} isLoading={saving}>Ayarları Kaydet</Button>
        </div>
      </div>
    </AppShell>
  )
}
