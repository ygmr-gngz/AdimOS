'use client'

import AppShell from '@/components/layout/AppShell'
import Card, { CardHeader, CardTitle } from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import Button from '@/components/ui/Button'
import { Key, Mic, Globe, Bell } from 'lucide-react'

export default function SettingsPage() {
  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in max-w-2xl">
        <div>
          <h2 className="text-xl font-bold text-white mb-1">Ayarlar</h2>
          <p className="text-sm text-gray-500">Sistem ve kullanıcı tercihlerinizi yönetin</p>
        </div>

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
