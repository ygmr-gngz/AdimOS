'use client'

import { useState } from 'react'
import AppShell from '@/components/layout/AppShell'
import Card, { CardHeader, CardTitle } from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import Button from '@/components/ui/Button'
import { Key, Mic, Globe, Bell, Lock, CheckCircle } from 'lucide-react'
import apiClient from '@/lib/api-client'
import toast from 'react-hot-toast'

function ChangePasswordCard() {
  const [form, setForm] = useState({ newPassword: '', confirm: '' })
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (form.newPassword.length < 8) {
      toast.error('Şifre en az 8 karakter olmalı')
      return
    }
    if (form.newPassword !== form.confirm) {
      toast.error('Şifreler eşleşmiyor')
      return
    }
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
          <button
            onClick={() => setDone(false)}
            className="ml-auto text-xs text-green-500 hover:text-green-300 transition-colors"
          >
            Tekrar değiştir
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Yeni Şifre"
            type="password"
            placeholder="En az 8 karakter"
            value={form.newPassword}
            onChange={(e) => setForm({ ...form, newPassword: e.target.value })}
          />
          <Input
            label="Yeni Şifre (Tekrar)"
            type="password"
            placeholder="Aynı şifreyi tekrar gir"
            value={form.confirm}
            onChange={(e) => setForm({ ...form, confirm: e.target.value })}
          />
          {form.newPassword && form.confirm && form.newPassword !== form.confirm && (
            <p className="text-xs text-red-400">Şifreler eşleşmiyor</p>
          )}
          <Button type="submit" isLoading={loading} disabled={loading}>
            Şifreyi Güncelle
          </Button>
        </form>
      )}
    </Card>
  )
}

export default function SettingsPage() {
  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in max-w-2xl">
        <div>
          <h2 className="text-xl font-bold text-white mb-1">Ayarlar</h2>
          <p className="text-sm text-gray-500">Sistem ve kullanıcı tercihlerinizi yönetin</p>
        </div>

        <ChangePasswordCard />

        <Card variant="bordered">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Key size={16} className="text-gray-400" />
              <CardTitle>API Anahtarları</CardTitle>
            </div>
          </CardHeader>
          <div className="space-y-4">
            <Input label="OpenAI API Key" type="password" placeholder="sk-..." />
            <Input label="Supabase URL" placeholder="https://xxx.supabase.co" />
            <Input label="Supabase Anon Key" type="password" placeholder="eyJ..." />
            <Button>Kaydet</Button>
          </div>
        </Card>

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
              <Globe size={16} className="text-gray-400" />
              <CardTitle>Sosyal Medya Bağlantıları</CardTitle>
            </div>
          </CardHeader>
          <div className="space-y-4">
            <Input label="YouTube Channel ID" placeholder="UC..." />
            <Input label="Instagram Business Account ID" placeholder="Instagram Business ID" />
            <Input label="Facebook / Meta API Token" type="password" placeholder="EAA..." />
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
