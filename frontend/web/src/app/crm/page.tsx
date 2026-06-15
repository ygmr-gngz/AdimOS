'use client'

import AppShell from '@/components/layout/AppShell'
import { Users, Plus } from 'lucide-react'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'

export default function CrmPage() {
  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-white mb-1">CRM</h2>
            <p className="text-sm text-gray-500">Lead ve müşteri takibi</p>
          </div>
          <Button>
            <Plus size={15} /> Yeni Lead
          </Button>
        </div>

        <div className="grid grid-cols-3 gap-4">
          {[
            { label: 'Toplam Lead', value: '0', color: 'bg-blue-500/20 text-blue-400' },
            { label: 'Aktif Görüşme', value: '0', color: 'bg-green-500/20 text-green-400' },
            { label: 'Bu Ay Kazanılan', value: '0', color: 'bg-purple-500/20 text-purple-400' },
          ].map((s) => (
            <div key={s.label} className="bg-surface-50 rounded-xl p-5 border border-surface-200">
              <p className="text-xs text-gray-500 mb-1">{s.label}</p>
              <p className="text-2xl font-bold text-white">{s.value}</p>
            </div>
          ))}
        </div>

        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="p-4 bg-surface-100 rounded-2xl mb-4">
            <Users size={40} className="text-gray-500" />
          </div>
          <p className="text-sm font-medium text-gray-400 mb-1">CRM modülü hazırlanıyor</p>
          <p className="text-xs text-gray-600">Lead ekleme, skorlama ve takip özellikleri yakında aktif olacak</p>
          <Badge variant="warning" className="mt-4">Faz 2</Badge>
        </div>
      </div>
    </AppShell>
  )
}
