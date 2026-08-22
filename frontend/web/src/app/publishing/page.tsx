'use client'

import { useEffect, useState } from 'react'
import AppShell from '@/components/layout/AppShell'
import apiClient from '@/lib/api-client'

interface QueueItem {
  id: string; platform: string; content_type: string; status: string
  scheduled_at?: string; published_at?: string; attempt_count: number; last_error?: string
}

const STATUS_LABELS: Record<string, string> = {
  pending: 'Bekleyen', scheduled: 'Zamanlanmış', publishing: 'Yayınlanıyor',
  published: 'Yayınlanmış', failed: 'Hatalı', cancelled: 'İptal',
}

export default function PublishingPage() {
  const [rows, setRows] = useState<QueueItem[]>([])
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    apiClient.get('/publishing/queue').then(({ data }) => setRows(data)).finally(() => setLoading(false))
  }, [])
  return <AppShell><div style={{ maxWidth: 1100, margin: '0 auto' }}>
    <h1 style={{ color: '#0B2A4A', fontSize: 28, fontWeight: 800 }}>Yayın Kuyruğu</h1>
    <p style={{ color: '#64748b' }}>Platform yayınları aynı platformda en az 4 saat arayla planlanır.</p>
    {loading ? <p>Yükleniyor…</p> : <div style={{ display: 'grid', gap: 12 }}>
      {rows.map(row => <article key={row.id} style={{ background: '#fff', border: `1px solid ${row.status === 'failed' ? '#fca5a5' : '#e2e8f0'}`, borderRadius: 12, padding: 16, display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
        <strong>{row.platform} · {row.content_type}</strong>
        <span>{STATUS_LABELS[row.status] || row.status}</span>
        <span>{row.scheduled_at ? new Date(row.scheduled_at).toLocaleString('tr-TR') : 'Slot bekliyor'}</span>
        {row.last_error && <p style={{ gridColumn: '1 / -1', color: '#b91c1c', margin: 0 }}>Deneme {row.attempt_count}/3: {row.last_error}</p>}
      </article>)}
      {!rows.length && <p style={{ color: '#94a3b8' }}>Yayın kuyruğu boş.</p>}
    </div>}
  </div></AppShell>
}
