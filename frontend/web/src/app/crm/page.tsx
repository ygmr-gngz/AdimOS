'use client'

import { useState, useEffect, useCallback } from 'react'
import AppShell from '@/components/layout/AppShell'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import { crmService, type Lead, type LeadStatus } from '@/services/crm.service'
import { Users, Plus, Trash2, Phone, Mail, X, AlertCircle, MessageCircle, Edit2 } from 'lucide-react'
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

const SERVICES = [
  'SMMM Danışmanlık', 'SGS Sınav Hazırlığı', 'Muhasebe Eğitimi',
  'Vergi Danışmanlığı', 'Mali Müşavirlik', 'Şirket Kuruluşu', 'Diğer',
]

interface FormData {
  name: string
  email: string
  phone: string
  status: LeadStatus
  source: string
  service_interest: string
  notes: string
}

interface FormErrors {
  name?: string
  email?: string
  phone?: string
  source?: string
}

const EMPTY: FormData = {
  name: '', email: '', phone: '', status: 'new',
  source: '', service_interest: '', notes: '',
}

// Türkiye telefon formatı: 0555 123 45 67 veya +90 555 123 45 67
function formatPhone(raw: string): string {
  let digits = raw.replace(/\D/g, '').slice(0, 12)

  // 90 ile başlayan 12 hane → uluslararası format
  if (digits.startsWith('90') && digits.length >= 10) {
    const local = digits.slice(2, 12)
    if (local.length <= 3) return `+90 ${local}`
    if (local.length <= 6) return `+90 ${local.slice(0, 3)} ${local.slice(3)}`
    if (local.length <= 8) return `+90 ${local.slice(0, 3)} ${local.slice(3, 6)} ${local.slice(6)}`
    return `+90 ${local.slice(0, 3)} ${local.slice(3, 6)} ${local.slice(6, 8)} ${local.slice(8)}`
  }

  // 5 ile başlayan 10 hane → 0 ekle
  if (digits.startsWith('5') && !digits.startsWith('90')) {
    digits = '0' + digits.slice(0, 10)
  }

  digits = digits.slice(0, 11)
  if (digits.length <= 4) return digits
  if (digits.length <= 7) return `${digits.slice(0, 4)} ${digits.slice(4)}`
  if (digits.length <= 9) return `${digits.slice(0, 4)} ${digits.slice(4, 7)} ${digits.slice(7)}`
  return `${digits.slice(0, 4)} ${digits.slice(4, 7)} ${digits.slice(7, 9)} ${digits.slice(9)}`
}

function normalizePhone(phone: string): string {
  const digits = phone.replace(/\D/g, '')
  if (digits.startsWith('90') && digits.length === 12) return `+${digits}`
  if (digits.startsWith('0') && digits.length === 11) return `+9${digits}`
  if (digits.startsWith('5') && digits.length === 10) return `+90${digits}`
  return phone
}

function phoneToDigits(phone: string): string {
  return phone.replace(/\D/g, '')
}

function validatePhone(phone: string): string | undefined {
  const digits = phone.replace(/\D/g, '')
  if (!digits) return 'Telefon zorunlu'
  if (digits.startsWith('90') && digits.length === 12) return undefined
  if (digits.startsWith('0') && digits.length === 11) return undefined
  if (digits.startsWith('5') && digits.length === 10) return undefined
  if (digits.startsWith('0')) return 'Telefon 11 haneli olmalı (0555 123 45 67)'
  return 'Geçerli bir Türkiye numarası girin (0555 123 45 67)'
}

function validateEmail(email: string): string | undefined {
  if (!email) return 'E-posta zorunlu'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return 'Geçerli e-posta girin'
}

function FieldError({ msg }: { msg?: string }) {
  if (!msg) return null
  return (
    <div className="flex items-center gap-1 mt-1">
      <AlertCircle size={11} className="text-red-400 shrink-0" />
      <span className="text-xs text-red-400">{msg}</span>
    </div>
  )
}

function LeadCard({ lead, onStatus, onDelete }: {
  lead: Lead
  onStatus: (id: string, s: LeadStatus) => void
  onDelete: (id: string) => void
}) {
  const rawDigits = phoneToDigits(lead.phone || '')
  const wa = rawDigits.startsWith('90') ? rawDigits : rawDigits.startsWith('0') ? `9${rawDigits}` : `90${rawDigits}`

  return (
    <div className="bg-surface-50 rounded-xl border border-surface-200 p-4 hover:border-surface-300 transition-colors group">
      {/* Header satırı */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-full bg-brand-600/20 flex items-center justify-center flex-shrink-0">
            <span className="text-sm font-bold text-brand-400">{lead.name[0].toUpperCase()}</span>
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-gray-200 truncate">{lead.name}</p>
            <p className="text-xs text-gray-500">{new Date(lead.created_at).toLocaleDateString('tr-TR')}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <Badge variant={STATUS_VARIANT[lead.status]} dot>
            {STATUS_LABELS[lead.status]}
          </Badge>
          <button
            onClick={() => onDelete(lead.id)}
            className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-500/20 text-gray-600 hover:text-red-400 transition-all"
          >
            <Trash2 size={13} />
          </button>
        </div>
      </div>

      {/* İletişim bilgileri */}
      <div className="space-y-1.5 mb-3">
        {lead.phone && (
          <div className="flex items-center gap-2">
            <Phone size={12} className="text-gray-600 shrink-0" />
            <span className="text-xs text-gray-400">{lead.phone}</span>
            <div className="flex items-center gap-1 ml-auto">
              <a
                href={`tel:${lead.phone}`}
                className="p-1 rounded bg-green-500/15 text-green-400 hover:bg-green-500/25 transition-colors"
                title="Ara"
              >
                <Phone size={11} />
              </a>
              <a
                href={`https://wa.me/${wa}`}
                target="_blank"
                rel="noopener noreferrer"
                className="p-1 rounded bg-green-500/15 text-green-400 hover:bg-green-500/25 transition-colors"
                title="WhatsApp"
              >
                <MessageCircle size={11} />
              </a>
            </div>
          </div>
        )}
        {lead.email && (
          <div className="flex items-center gap-2">
            <Mail size={12} className="text-gray-600 shrink-0" />
            <a href={`mailto:${lead.email}`} className="text-xs text-gray-400 hover:text-brand-400 truncate transition-colors">
              {lead.email}
            </a>
          </div>
        )}
      </div>

      {/* Etiketler */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {lead.source && (
          <span className="text-[10px] bg-surface-200 text-gray-500 px-2 py-0.5 rounded-full">{lead.source}</span>
        )}
        {lead.notes?.startsWith('Hizmet İlgisi:') && (
          <span className="text-[10px] bg-brand-600/15 text-brand-400 px-2 py-0.5 rounded-full">
            {lead.notes.split('\n')[0].replace('Hizmet İlgisi: ', '')}
          </span>
        )}
      </div>

      {/* Not */}
      {lead.notes && !lead.notes.startsWith('Hizmet İlgisi:') && (
        <p className="text-xs text-gray-600 mb-3 line-clamp-2">{lead.notes}</p>
      )}

      {/* Durum değiştir */}
      <select
        value={lead.status}
        onChange={e => onStatus(lead.id, e.target.value as LeadStatus)}
        className="w-full bg-surface-100 border border-surface-200 rounded-lg px-2 py-1.5 text-xs text-gray-300 focus:outline-none focus:ring-1 focus:ring-brand-500"
      >
        {(Object.keys(STATUS_LABELS) as LeadStatus[]).map(s => (
          <option key={s} value={s}>{STATUS_LABELS[s]}</option>
        ))}
      </select>
    </div>
  )
}

export default function CrmPage() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<FormData>(EMPTY)
  const [errors, setErrors] = useState<FormErrors>({})
  const [saving, setSaving] = useState(false)
  const [touched, setTouched] = useState<Set<string>>(new Set())

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

  const validate = (f: FormData): FormErrors => ({
    name: !f.name.trim() ? 'Ad Soyad zorunlu' : undefined,
    email: validateEmail(f.email),
    phone: validatePhone(f.phone),
    source: !f.source ? 'Kaynak seçin' : undefined,
  })

  const handlePhoneChange = (raw: string) => {
    const formatted = formatPhone(raw)
    setForm(prev => ({ ...prev, phone: formatted }))
    if (touched.has('phone')) {
      setErrors(prev => ({ ...prev, phone: validatePhone(formatted) }))
    }
  }

  const handleBlur = (field: keyof FormErrors) => {
    setTouched(prev => new Set(prev).add(field))
    setErrors(prev => ({ ...prev, [field]: validate(form)[field] }))
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setTouched(new Set(['name', 'email', 'phone', 'source']))
    const errs = validate(form)
    setErrors(errs)
    if (Object.values(errs).some(Boolean)) {
      toast.error('Formdaki hataları düzeltin')
      return
    }
    setSaving(true)
    try {
      const notes = [
        form.service_interest ? `Hizmet İlgisi: ${form.service_interest}` : '',
        form.notes,
      ].filter(Boolean).join('\n')

      const lead = await crmService.create({
        name: form.name.trim(),
        email: form.email.trim(),
        phone: normalizePhone(form.phone),
        status: form.status,
        source: form.source,
        notes: notes || undefined,
      })
      setLeads(prev => [lead, ...prev])
      setForm(EMPTY)
      setErrors({})
      setTouched(new Set())
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
      setLeads(prev => prev.map(l => l.id === id ? updated : l))
    } catch {
      toast.error('Durum güncellenemedi')
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await crmService.delete(id)
      setLeads(prev => prev.filter(l => l.id !== id))
      toast.success('Lead silindi')
    } catch {
      toast.error('Silinemedi')
    }
  }

  const fieldClass = (hasError: boolean) =>
    `w-full bg-surface-100 border rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 transition-colors ${
      hasError ? 'border-red-500/50 focus:ring-red-500/30' : 'border-surface-200 focus:ring-brand-500'
    }`

  const counts = {
    total: leads.length,
    active: leads.filter(l => l.status === 'contacted' || l.status === 'new').length,
    qualified: leads.filter(l => l.status === 'qualified').length,
  }

  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-white mb-1">CRM</h2>
            <p className="text-sm text-gray-500">Danışan adayları ve müşteri takibi</p>
          </div>
          <Button onClick={() => { setShowForm(true); setForm(EMPTY); setErrors({}); setTouched(new Set()) }}>
            <Plus size={15} /> Yeni Lead
          </Button>
        </div>

        {/* Sayaçlar */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Toplam Lead', value: counts.total },
            { label: 'Aktif Görüşme', value: counts.active },
            { label: 'Nitelikli', value: counts.qualified },
          ].map(({ label, value }) => (
            <div key={label} className="bg-surface-50 rounded-xl p-4 border border-surface-200">
              <p className="text-xs text-gray-500 mb-1">{label}</p>
              <p className="text-xl font-bold text-white">{value}</p>
            </div>
          ))}
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

            <form onSubmit={handleCreate} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5">
                  Ad Soyad <span className="text-red-400">*</span>
                </label>
                <input
                  value={form.name}
                  onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
                  onBlur={() => handleBlur('name')}
                  placeholder="Ahmet Yılmaz"
                  className={fieldClass(!!errors.name && touched.has('name'))}
                />
                {touched.has('name') && <FieldError msg={errors.name} />}
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5">
                  Telefon <span className="text-red-400">*</span>
                </label>
                <input
                  value={form.phone}
                  onChange={e => handlePhoneChange(e.target.value)}
                  onBlur={() => handleBlur('phone')}
                  placeholder="0555 123 45 67"
                  inputMode="numeric"
                  className={fieldClass(!!errors.phone && touched.has('phone'))}
                />
                {touched.has('phone') && <FieldError msg={errors.phone} />}
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5">
                  E-posta <span className="text-red-400">*</span>
                </label>
                <input
                  type="email"
                  value={form.email}
                  onChange={e => setForm(p => ({ ...p, email: e.target.value }))}
                  onBlur={() => handleBlur('email')}
                  placeholder="ahmet@email.com"
                  className={fieldClass(!!errors.email && touched.has('email'))}
                />
                {touched.has('email') && <FieldError msg={errors.email} />}
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5">
                  Kaynak <span className="text-red-400">*</span>
                </label>
                <select
                  value={form.source}
                  onChange={e => { setForm(p => ({ ...p, source: e.target.value })); setTouched(prev => new Set(prev).add('source')) }}
                  onBlur={() => handleBlur('source')}
                  className={fieldClass(!!errors.source && touched.has('source'))}
                >
                  <option value="">Seç...</option>
                  <option value="instagram">Instagram</option>
                  <option value="youtube">YouTube</option>
                  <option value="website">Website</option>
                  <option value="referans">Referans</option>
                  <option value="telefon">Telefon</option>
                  <option value="diger">Diğer</option>
                </select>
                {touched.has('source') && <FieldError msg={errors.source} />}
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5">Durum</label>
                <select
                  value={form.status}
                  onChange={e => setForm(p => ({ ...p, status: e.target.value as LeadStatus }))}
                  className={fieldClass(false)}
                >
                  {(Object.keys(STATUS_LABELS) as LeadStatus[]).map(s => (
                    <option key={s} value={s}>{STATUS_LABELS[s]}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5">Hizmet İlgisi</label>
                <select
                  value={form.service_interest}
                  onChange={e => setForm(p => ({ ...p, service_interest: e.target.value }))}
                  className={fieldClass(false)}
                >
                  <option value="">Seç...</option>
                  {SERVICES.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>

              <div className="col-span-1 sm:col-span-2">
                <label className="block text-xs font-medium text-gray-400 mb-1.5">Not</label>
                <textarea
                  value={form.notes}
                  onChange={e => setForm(p => ({ ...p, notes: e.target.value }))}
                  rows={2}
                  placeholder="Danışan hakkında not..."
                  className="w-full bg-surface-100 border border-surface-200 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
                />
              </div>

              <div className="col-span-1 sm:col-span-2 flex items-center justify-between">
                <p className="text-xs text-gray-600"><span className="text-red-400">*</span> zorunlu alan</p>
                <div className="flex gap-2">
                  <Button type="button" variant="secondary" onClick={() => setShowForm(false)}>İptal</Button>
                  <Button type="submit" isLoading={saving}>Ekle</Button>
                </div>
              </div>
            </form>
          </div>
        )}

        {/* Lead listesi */}
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
            <p className="text-sm font-medium text-gray-400 mb-4">Henüz lead yok</p>
            <Button onClick={() => setShowForm(true)} variant="secondary">
              <Plus size={15} /> İlk Leadi Ekle
            </Button>
          </div>
        ) : (
          <>
            {/* Mobil: kart grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:hidden">
              {leads.map(lead => (
                <LeadCard key={lead.id} lead={lead} onStatus={handleStatus} onDelete={handleDelete} />
              ))}
            </div>

            {/* Desktop: satır listesi */}
            <div className="hidden md:block space-y-2">
              {leads.map(lead => {
                const rawDigits = phoneToDigits(lead.phone || '')
                const wa = rawDigits.startsWith('90') ? rawDigits : rawDigits.startsWith('0') ? `9${rawDigits}` : `90${rawDigits}`
                return (
                  <div
                    key={lead.id}
                    className="flex items-center gap-4 p-4 bg-surface-50 rounded-xl border border-surface-200 hover:border-surface-300 transition-colors group"
                  >
                    <div className="w-9 h-9 rounded-full bg-brand-600/20 flex items-center justify-center flex-shrink-0">
                      <span className="text-sm font-bold text-brand-400">{lead.name[0].toUpperCase()}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-200">{lead.name}</p>
                      <div className="flex items-center gap-3 mt-0.5 flex-wrap">
                        <span className="text-xs text-gray-500 flex items-center gap-1">
                          <Mail size={10} />{lead.email}
                        </span>
                        {lead.phone && (
                          <span className="text-xs text-gray-500 flex items-center gap-1">
                            <Phone size={10} />{lead.phone}
                          </span>
                        )}
                        {lead.source && (
                          <span className="text-xs bg-surface-100 text-gray-500 px-1.5 py-0.5 rounded-full">{lead.source}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {lead.phone && (
                        <>
                          <a href={`tel:${lead.phone}`} className="p-1.5 rounded-lg text-gray-600 hover:text-green-400 hover:bg-green-500/10 transition-colors" title="Ara">
                            <Phone size={14} />
                          </a>
                          <a href={`https://wa.me/${wa}`} target="_blank" rel="noopener noreferrer" className="p-1.5 rounded-lg text-gray-600 hover:text-green-400 hover:bg-green-500/10 transition-colors" title="WhatsApp">
                            <MessageCircle size={14} />
                          </a>
                        </>
                      )}
                      <select
                        value={lead.status}
                        onChange={e => handleStatus(lead.id, e.target.value as LeadStatus)}
                        className="bg-surface-100 border border-surface-200 rounded-lg px-2 py-1 text-xs text-gray-300 focus:outline-none"
                      >
                        {(Object.keys(STATUS_LABELS) as LeadStatus[]).map(s => (
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
                )
              })}
            </div>
          </>
        )}
      </div>
    </AppShell>
  )
}
