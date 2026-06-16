'use client'

import { useState, useEffect } from 'react'
import AppShell from '@/components/layout/AppShell'
import { useAuth } from '@/hooks/useAuth'
import apiClient from '@/lib/api-client'
import toast from 'react-hot-toast'
import { UserPlus, Shield, User, Trash2, Copy } from 'lucide-react'

interface UserProfile {
  id: string
  user_id: string
  display_name: string | null
  role: 'admin' | 'editor'
  is_active: boolean
  created_at: string
}

export default function UsersPage() {
  const { profile } = useAuth()
  const [users, setUsers] = useState<UserProfile[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ email: '', display_name: '', role: 'editor' })
  const [createdPassword, setCreatedPassword] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (profile?.role !== 'admin') return
    apiClient.get('/users')
      .then(({ data }) => setUsers(data.users ?? []))
      .catch(() => toast.error('Kullanıcılar yüklenemedi'))
      .finally(() => setIsLoading(false))
  }, [profile])

  const handleCreate = async (e: { preventDefault: () => void }) => {
    e.preventDefault()
    setIsSubmitting(true)
    try {
      const { data } = await apiClient.post('/users', form)
      setCreatedPassword(data.temporary_password)
      setUsers((prev) => [...prev, { id: data.user_id, user_id: data.user_id, display_name: form.display_name, role: form.role as 'admin' | 'editor', is_active: true, created_at: new Date().toISOString() }])
      setForm({ email: '', display_name: '', role: 'editor' })
      setShowForm(false)
      toast.success('Kullanıcı oluşturuldu')
    } catch {
      toast.error('Kullanıcı oluşturulamadı')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleRoleChange = async (userId: string, newRole: string) => {
    try {
      await apiClient.put(`/users/${userId}/role`, { role: newRole })
      setUsers((prev) => prev.map((u) => u.user_id === userId ? { ...u, role: newRole as 'admin' | 'editor' } : u))
      toast.success('Rol güncellendi')
    } catch {
      toast.error('Rol güncellenemedi')
    }
  }

  const handleDeactivate = async (userId: string) => {
    if (!confirm('Bu kullanıcıyı devre dışı bırakmak istiyor musunuz?')) return
    try {
      await apiClient.delete(`/users/${userId}`)
      setUsers((prev) => prev.map((u) => u.user_id === userId ? { ...u, is_active: false } : u))
      toast.success('Kullanıcı devre dışı bırakıldı')
    } catch {
      toast.error('İşlem başarısız')
    }
  }

  if (profile?.role !== 'admin') {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500 text-sm">Bu sayfaya erişim yetkiniz yok.</p>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-white mb-1">Kullanıcı Yönetimi</h2>
            <p className="text-sm text-gray-500">Panel kullanıcılarını ve rollerini yönetin</p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium rounded-xl transition-colors"
          >
            <UserPlus size={15} />
            Kullanıcı Ekle
          </button>
        </div>

        {createdPassword && (
          <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4">
            <p className="text-sm text-green-400 font-medium mb-1">Kullanıcı oluşturuldu!</p>
            <p className="text-xs text-green-300">Geçici şifre: <span className="font-mono bg-green-500/20 px-2 py-0.5 rounded">{createdPassword}</span></p>
            <button
              onClick={() => { navigator.clipboard.writeText(createdPassword); toast.success('Kopyalandı') }}
              className="mt-2 flex items-center gap-1 text-xs text-green-400 hover:text-green-300"
            >
              <Copy size={12} /> Kopyala
            </button>
            <p className="text-xs text-green-600 mt-1">Bu şifreyi kullanıcıya iletin. İlk girişte değiştirmesi gerekecek.</p>
          </div>
        )}

        {showForm && (
          <form onSubmit={handleCreate} className="bg-surface-50 border border-surface-200 rounded-xl p-5 space-y-4">
            <h3 className="text-sm font-semibold text-gray-200">Yeni Kullanıcı</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Ad Soyad</label>
                <input
                  value={form.display_name}
                  onChange={(e) => setForm({ ...form, display_name: e.target.value })}
                  required
                  placeholder="Yağmur Güngöz"
                  className="w-full px-3 py-2 bg-surface-100 border border-surface-300 rounded-lg text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-brand-500 transition-colors"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">E-posta</label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  required
                  placeholder="ornek@adim.com"
                  className="w-full px-3 py-2 bg-surface-100 border border-surface-300 rounded-lg text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-brand-500 transition-colors"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Rol</label>
              <select
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
                className="w-full px-3 py-2 bg-surface-100 border border-surface-300 rounded-lg text-sm text-gray-100 focus:outline-none focus:border-brand-500 transition-colors"
              >
                <option value="editor">Editör — İçerik üretir, onaya gönderir</option>
                <option value="admin">Admin — Tüm modüllere erişir</option>
              </select>
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
              >
                {isSubmitting ? 'Oluşturuluyor...' : 'Oluştur'}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 bg-surface-100 hover:bg-surface-200 text-gray-400 text-sm font-medium rounded-lg transition-colors"
              >
                İptal
              </button>
            </div>
          </form>
        )}

        {isLoading ? (
          <div className="flex justify-center py-10">
            <svg className="animate-spin h-5 w-5 text-brand-400" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        ) : (
          <div className="space-y-2">
            {users.map((u) => (
              <div
                key={u.user_id}
                className={`flex items-center justify-between p-4 rounded-xl border transition-colors ${u.is_active ? 'bg-surface-50 border-surface-200' : 'bg-surface-50/50 border-surface-200/50 opacity-60'}`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-500/40 to-brand-700/40 border border-brand-600/30 flex items-center justify-center text-xs font-bold text-brand-400">
                    {(u.display_name?.[0] ?? 'U').toUpperCase()}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-200">{u.display_name ?? '—'}</p>
                    <p className="text-xs text-gray-500">{new Date(u.created_at).toLocaleDateString('tr-TR')}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <select
                    value={u.role}
                    onChange={(e) => handleRoleChange(u.user_id, e.target.value)}
                    disabled={!u.is_active}
                    className="px-2 py-1 bg-surface-100 border border-surface-300 rounded-lg text-xs text-gray-300 focus:outline-none focus:border-brand-500 transition-colors"
                  >
                    <option value="editor">Editör</option>
                    <option value="admin">Admin</option>
                  </select>
                  <span className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full ${u.role === 'admin' ? 'bg-brand-600/20 text-brand-400' : 'bg-surface-100 text-gray-400'}`}>
                    {u.role === 'admin' ? <Shield size={10} /> : <User size={10} />}
                    {u.role === 'admin' ? 'Admin' : 'Editör'}
                  </span>
                  {u.is_active && (
                    <button
                      onClick={() => handleDeactivate(u.user_id)}
                      className="p-1.5 rounded-lg text-gray-600 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                      title="Devre dışı bırak"
                    >
                      <Trash2 size={13} />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  )
}
