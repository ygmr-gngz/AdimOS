'use client'

import { useState } from 'react'
import AppShell from '@/components/layout/AppShell'
import Card, { CardHeader, CardTitle } from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import Button from '@/components/ui/Button'
import { Mic, Globe, Bell, Lock, CheckCircle, AlertCircle, Instagram, Youtube, RefreshCw } from 'lucide-react'
import apiClient from '@/lib/api-client'
import toast from 'react-hot-toast'

/* ─── Şifre Değiştir ─────────────────────────────────────────── */
function ChangePasswordCard() {
  const [form, setForm] = useState({ newPassword: '', confirm: '' })
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (form.newPassword.length < 8) { toast.error('Şifre en az 8 karakter olmalı'); return }
    if (form.newPassword !== form.confirm) { toast.error('Şifreler eşleşmiyor'); return }
    setLoading(true)
    try {
      await apiClient.post('/users/me/change-password', { new_password: form.newPassword })
      setDone(true)
      setForm({ newPassword: '', confirm: '' })
      toast.success('Şifre güncellendi')
    } catch {
      toast.error('Şifre değiştirilemedi')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card variant="bordered">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Lock size={16} className="text-gray-400" />
          <CardTitle>Şifre Değiştir</CardTitle>
        </div>
      </CardHeader>
      {done ? (
        <div className="flex items-center gap-3 p-4 bg-green-500/10 rounded-xl border border-green-500/20">
          <CheckCircle size={18} className="text-green-400 shrink-0" />
          <div>
            <p className="text-sm font-medium text-green-300">Şifre güncellendi</p>
            <p className="text-xs text-green-600 mt-0.5">Bir sonraki girişte yeni şifreni kullan.</p>
          </div>
          <button onClick={() => setDone(false)} className="ml-auto text-xs text-green-500 hover:text-green-300 transition-colors">
            Tekrar değiştir
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Yeni Şifre" type="password" placeholder="En az 8 karakter"
            value={form.newPassword} onChange={(e) => setForm({ ...form, newPassword: e.target.value })} />
          <Input label="Yeni Şifre (Tekrar)" type="password" placeholder="Aynı şifreyi tekrar gir"
            value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} />
          {form.newPassword && form.confirm && form.newPassword !== form.confirm && (
            <p className="text-xs text-red-400">Şifreler eşleşmiyor</p>
          )}
          <Button type="submit" isLoading={loading} disabled={loading}>Şifreyi Güncelle</Button>
        </form>
      )}
    </Card>
  )
}

/* ─── Sosyal Medya Bağlantıları ──────────────────────────────── */
interface InstagramStatus {
  token_configured: boolean
  account_configured: boolean
  token_preview: string
  account_id: string | null
  connected: boolean
  account_name: string | null
  followers: number | null
  error: string | null
}

interface YoutubeStatus {
  connected: boolean
  source: 'env' | 'supabase' | null
  client_id_configured: boolean
  error: string | null
}

function StatusBadge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span className={`flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${
      ok ? 'bg-green-500/15 text-green-400' : 'bg-red-500/15 text-red-400'
    }`}>
      {ok ? <CheckCircle size={11} /> : <AlertCircle size={11} />}
      {label}
    </span>
  )
}

function SocialConnectionCard() {
  const [igStatus, setIgStatus] = useState<InstagramStatus | null>(null)
  const [ytStatus, setYtStatus] = useState<YoutubeStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [ytConnecting, setYtConnecting] = useState(false)

  const testConnections = async () => {
    setLoading(true)
    try {
      const [igRes, ytRes] = await Promise.all([
        apiClient.get('/social/instagram/status'),
        apiClient.get('/social/youtube/status'),
      ])
      setIgStatus(igRes.data)
      setYtStatus(ytRes.data)
    } catch {
      toast.error('Bağlantı durumu alınamadı')
    } finally {
      setLoading(false)
    }
  }

  const handleYouTubeConnect = async () => {
    setYtConnecting(true)
    try {
      const { data } = await apiClient.get('/social/youtube/auth-url')
      window.open(data.auth_url, '_blank', 'width=600,height=700')
      toast.success('Google giriş penceresi açıldı. Giriş yaptıktan sonra durumu yenileyin.')
      setTimeout(testConnections, 8000)
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      toast.error(e?.response?.data?.detail ?? 'Auth URL alınamadı')
    } finally {
      setYtConnecting(false)
    }
  }

  return (
    <Card variant="bordered">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Globe size={16} className="text-gray-400" />
            <CardTitle>Sosyal Medya Bağlantıları</CardTitle>
          </div>
          <Button size="sm" variant="secondary" onClick={testConnections} isLoading={loading}>
            <RefreshCw size={13} /> Durumu Test Et
          </Button>
        </div>
      </CardHeader>

      <div className="space-y-5">
        {/* Instagram */}
        <div className="p-4 bg-surface-100 rounded-xl border border-surface-200">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Instagram size={16} className="text-pink-400" />
              <span className="text-sm font-semibold text-gray-200">Instagram Business</span>
            </div>
            {igStatus && (
              <StatusBadge ok={igStatus.connected} label={igStatus.connected ? 'Bağlı' : 'Bağlantı Yok'} />
            )}
          </div>

          {igStatus ? (
            <div className="space-y-2">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="flex items-center gap-1.5 text-gray-400">
                  <span className="text-gray-600">Token:</span>
                  <code className="text-gray-300 bg-surface-200 px-1.5 py-0.5 rounded">{igStatus.token_preview}</code>
                  <StatusBadge ok={igStatus.token_configured} label={igStatus.token_configured ? 'Var' : 'Yok'} />
                </div>
                <div className="flex items-center gap-1.5 text-gray-400">
                  <span className="text-gray-600">Account ID:</span>
                  <code className="text-gray-300 bg-surface-200 px-1.5 py-0.5 rounded text-[10px]">
                    {igStatus.account_id ?? '—'}
                  </code>
                </div>
              </div>
              {igStatus.connected && igStatus.account_name && (
                <div className="p-2.5 bg-green-500/10 border border-green-500/20 rounded-lg">
                  <p className="text-xs text-green-300">
                    <strong>{igStatus.account_name}</strong> hesabına bağlı
                    {igStatus.followers && ` · ${igStatus.followers.toLocaleString('tr-TR')} takipçi`}
                  </p>
                </div>
              )}
              {igStatus.error && (
                <div className="p-2.5 bg-red-500/10 border border-red-500/20 rounded-lg">
                  <p className="text-xs text-red-400">{igStatus.error}</p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-xs text-gray-600">
              Railway &rarr; Variables&apos;da <code className="text-gray-400">META_ACCESS_TOKEN</code> ve{' '}
              <code className="text-gray-400">INSTAGRAM_BUSINESS_ACCOUNT_ID</code> tanımlanmalı.{' '}
              <strong className="text-brand-400">Durumu Test Et</strong> butonuna basarak bağlantıyı kontrol edin.
            </p>
          )}
        </div>

        {/* YouTube */}
        <div className="p-4 bg-surface-100 rounded-xl border border-surface-200">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Youtube size={16} className="text-red-400" />
              <span className="text-sm font-semibold text-gray-200">YouTube</span>
            </div>
            <div className="flex items-center gap-2">
              {ytStatus && (
                <StatusBadge ok={ytStatus.connected} label={ytStatus.connected ? 'Bağlı' : 'Bağlantı Yok'} />
              )}
              {ytStatus && !ytStatus.connected && (
                <Button size="sm" onClick={handleYouTubeConnect} isLoading={ytConnecting}>
                  <Youtube size={12} /> Bağlan
                </Button>
              )}
            </div>
          </div>

          {ytStatus ? (
            <div className="space-y-2">
              {ytStatus.connected ? (
                <div className="p-2.5 bg-green-500/10 border border-green-500/20 rounded-lg">
                  <p className="text-xs text-green-300">
                    YouTube bağlı
                    {ytStatus.source === 'supabase' && ' · OAuth ile bağlandı'}
                    {ytStatus.source === 'env' && ' · Railway env var'}
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {ytStatus.error && (
                    <p className="text-xs text-red-400">{ytStatus.error}</p>
                  )}
                  <p className="text-xs text-gray-500">
                    <strong className="text-gray-300">Önkoşul:</strong> Railway&apos;e{' '}
                    <code className="text-gray-400">YOUTUBE_CLIENT_ID</code> ve{' '}
                    <code className="text-gray-400">YOUTUBE_CLIENT_SECRET</code> eklenmiş olmalı.
                    Sonra <strong className="text-brand-400">Bağlan</strong> butonuna bas.
                  </p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-xs text-gray-600">
              Durumu görmek için <strong className="text-brand-400">Durumu Test Et</strong> butonuna bas.
            </p>
          )}
        </div>

        {/* Nasıl yapılır */}
        <div className="p-3 bg-surface-200/50 rounded-xl text-xs text-gray-500 space-y-1">
          <p className="font-medium text-gray-400">Credentials nasıl güncellenir?</p>
          <p>1. Railway dashboard → Projeniz → Variables sekmesi</p>
          <p>2. İlgili değişkeni bulun veya yeni ekleyin</p>
          <p>3. Kaydedin → Railway otomatik redeploy yapar</p>
          <p>4. Burada <strong>Durumu Test Et</strong> butonuyla doğrulayın</p>
        </div>
      </div>
    </Card>
  )
}

/* ─── Ana Sayfa ──────────────────────────────────────────────── */
export default function SettingsPage() {
  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in max-w-2xl">
        <div>
          <h2 className="text-xl font-bold text-white mb-1">Ayarlar</h2>
          <p className="text-sm text-gray-500">Sistem ve kullanıcı tercihlerinizi yönetin</p>
        </div>

        <ChangePasswordCard />

        <SocialConnectionCard />

        <Card variant="bordered">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Mic size={16} className="text-gray-400" />
              <CardTitle>Ses Ayarları</CardTitle>
            </div>
          </CardHeader>
          <div className="space-y-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-300">TTS Sesi</label>
              <select className="bg-surface-100 border border-surface-200 rounded-lg px-3 py-2.5 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500">
                <option value="alloy">Alloy (Nötr)</option>
                <option value="nova">Nova (Kadın)</option>
                <option value="onyx">Onyx (Erkek)</option>
                <option value="shimmer">Shimmer (Yumuşak)</option>
              </select>
            </div>
            <Button>Kaydet</Button>
          </div>
        </Card>

        <Card variant="bordered">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Bell size={16} className="text-gray-400" />
              <CardTitle>Bildirimler</CardTitle>
            </div>
          </CardHeader>
          <div className="space-y-3">
            {[
              { label: 'Yeni içerik onay bekliyor', defaultChecked: true },
              { label: 'Doküman indekslendi', defaultChecked: true },
              { label: 'Agent hatası', defaultChecked: true },
              { label: 'Yeni lead eklendi', defaultChecked: false },
            ].map((n) => (
              <label key={n.label} className="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" defaultChecked={n.defaultChecked}
                  className="w-4 h-4 rounded border-surface-200 bg-surface-100 text-brand-600 focus:ring-brand-500"
                />
                <span className="text-sm text-gray-300">{n.label}</span>
              </label>
            ))}
            <Button className="mt-2">Kaydet</Button>
          </div>
        </Card>
      </div>
    </AppShell>
  )
}
