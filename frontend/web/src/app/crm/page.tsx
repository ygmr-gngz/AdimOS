'use client'

import { useState, useEffect, useCallback } from 'react'
import AppShell from '@/components/layout/AppShell'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import Input from '@/components/ui/Input'
import { crmService, type Lead, type LeadCreate, type LeadStatus } from '@/services/crm.service'
import { Users, Plus, Trash2, Phone, Mail, X } from 'lucide-react'
import toast from 'react-hot-toast'

const STATUS_LABELS: Record<LeadStatus, string> = {
  new: 'Yeni',
  contacted: 'İletişimde',
  qualified: 'Nitelikli',
  lost: 'Kayıp',
}

const STATUS_VARIANT: Record<LeadStatus, 'info' | 'warning' | 'success' | 'error'> = {
  new: 'info',
  contacted: 'warning',
  qualified: 'success',
  lost: 'error',
}

const EMPTY: LeadCreate = { name: '', email: '', phone: '', status: 'new', source: '', notes: '' }

export default function CrmPage() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<LeadCreate>(EMPTY)
  const [saving, setSaving] = useState(false)

  const fetchLeads = useCallback(async () => {
    try {
      const data = await crmService.list()
      setLeads(data)
    } catch {
      toast.error('Lead\'ler yüklenemedi')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { fetchLeads() }, [fetchLeads])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name || !form.email) return toast.error('Ad ve email zorunlu')
    setSaving(true)
    try {
      const lead = await crmService.create(form)
      setLeads((prev) => [lead, ...prev])
      setForm(EMPTY)
      setShowForm(false)
      toast.success('Lead eklendi')
    } catch {
      toast.error('Lead eklenemedi')
    } finally {
      setSaving(false)
    }
  }

  const handleStatus = async (id: string, status: LeadStatus) => {
    try {
      const updated = await crmService.updateStatus(id, status)
      setLeads((prev) => prev.map((l) => l.id === id ? updated : l))
    } catch {
      toast.error('Durum güncellenemedi')
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await crmService.delete(id)
      setLeads((prev) => prev.filter((l) => l.id !== id))
      toast.success('Lead silindi')
    } catch {
      toast.error('Silinemedi')
    }
  }

  const counts = {
    total: leads.length,
    active: leads.filter((l) => l.status === 'contacted' || l.status === 'new').length,
    qualified: leads.filter((l) => l.status === 'qualified').length,
  }

  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-white mb-1">CRM</h2>
            <p className="text-sm text-gray-500">Danışan adayları ve müşteri takibi</p>
          </div>
          <Button onClick={() => setShowForm(true)}>
            <Plus size={15} /> Yeni Lead
          </Button>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="bg-surface-50 rounded-xl p-5 border border-surface-200">
            <p className="text-xs text-gray-500 mb-1">Toplam Lead</p>
            <p className="text-2xl font-bold text-white">{counts.total}</p>
          </div>
          <div className="bg-surface-50 rounded-xl p-5 border border-surface-200">
            <p className="text-xs text-gray-500 mb-1">Aktif Görüşme</p>
            <p className="text-2xl font-bold text-white">{counts.active}</p>
          </div>
          <div className="bg-surface-50 rounded-xl p-5 border border-surface-200">
            <p className="text-xs text-gray-500 mb-1">Nitelikli</p>
            <p className="text-2xl font-bold text-white">{counts.qualified}</p>
          </div>
        </div>

        {/* Yeni Lead Formu */}
        {showForm && (
          <div className="bg-surface-50 border border-surface-200 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-200">Yeni Lead Ekle</h3>
              <button onClick={() => setShowForm(false)} className="text-gray-500 hover:text-gray-300">
                <X size={16} />
              </button>
            </div>
            <form onSubmit={handleCreate} className="grid grid-cols-2 gap-3">
              <Input
                label="Ad Soyad *"
                placeholder="Ahmet Yılmaz"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
              <Input
                label="E-posta *"
                type="email"
                placeholder="ahmet@email.com"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
              />
              <Input
                label="Telefon"
                placeholder="0532 000 00 00"
                value={form.phone ?? ''}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5">Kaynak</label>
                <select
                  value={form.source ?? ''}
                  onChange={(e) => setForm({ ...form, source: e.target.value })}
                  className="w-full bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="">Seç</option>
                  <option value="instagram">Instagram</option>
                  <option value="youtube">YouTube</option>
                  <option value="website">Website</option>
                  <option value="referans">Referans</option>
                  <option value="diger">Diğer</option>
                </select>
              </div>
              <div className="col-span-2">
                <label className="block text-xs font-medium text-gray-400 mb-1.5">Not</label>
                <textarea
                  value={form.notes ?? ''}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  rows={2}
                  placeholder="Danışan hakkında not..."
                  className="w-full bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
                />
              </div>
              <div className="col-span-2 flex gap-2 justify-end">
                <Button type="button" variant="secondary" onClick={() => setShowForm(false)}>İptal</Button>
                <Button type="submit" isLoading={saving}>Ekle</Button>
              </div>
            </form>
          </div>
        )}

        {/* Lead Listesi */}
        {isLoading ? (
          <div className="flex justify-center py-16">
            <svg className="animate-spin h-6 w-6 text-brand-400" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        ) : leads.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="p-4 bg-surface-100 rounded-2xl mb-4">
              <Users size={40} className="text-gray-500" />
            </div>
            <p className="text-sm font-medium text-gray-400 mb-1">Henüz lead yok</p>
            <p className="text-xs text-gray-600 mb-4">Yeni Lead butonuyla ekleyin veya sosyal medya API bağlandığında otomatik gelir</p>
            <Button onClick={() => setShowForm(true)} variant="secondary"><Plus size={15} /> İlk Leadi Ekle</Button>
          </div>
        ) : (
          <div className="space-y-2">
            {leads.map((lead) => (
              <div key={lead.id} className="flex items-center gap-4 p-4 bg-surface-50 rounded-xl border border-surface-200 hover:border-surface-300 transition-colors group">
                <div className="w-9 h-9 rounded-full bg-brand-600/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-bold text-brand-400">{lead.name[0].toUpperCase()}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-200">{lead.name}</p>
                  <div className="flex items-center gap-3 mt-0.5">
                    <span className="text-xs text-gray-500 flex items-center gap-1"><Mail size={10} />{lead.email}</span>
                    {lead.phone && <span className="text-xs text-gray-500 flex items-center gap-1"><Phone size={10} />{lead.phone}</span>}
                    {lead.source && <span className="text-xs text-gray-600">{lead.source}</span>}
                  </div>
                  {lead.notes && <p className="text-xs text-gray-600 mt-1 truncate">{lead.notes}</p>}
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={lead.status}
                    onChange={(e) => handleStatus(lead.id, e.target.value as LeadStatus)}
                    className="bg-surface-100 border border-surface-200 rounded-lg px-2 py-1 text-xs text-gray-300 focus:outline-none"
                  >
                    {(Object.keys(STATUS_LABELS) as LeadStatus[]).map((s) => (
                      <option key={s} value={s}>{STATUS_LABELS[s]}</option>
                    ))}
                  </select>
                  <Badge variant={STATUS_VARIANT[lead.status]} dot>{STATUS_LABELS[lead.status]}</Badge>
                  <span className="text-xs text-gray-600">{new Date(lead.created_at).toLocaleDateString('tr-TR')}</span>
                  <button
                    onClick={() => handleDelete(lead.id)}
                    className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-500/20 text-gray-600 hover:text-red-400 transition-all"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  )
}
