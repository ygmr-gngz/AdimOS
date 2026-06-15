'use client'

import AppShell from '@/components/layout/AppShell'
import { BarChart2, TrendingUp, FileText, Users } from 'lucide-react'

const cards = [
  { label: 'Doküman Analizi', desc: 'Yükleme trendi, indeksleme süreleri', icon: FileText, color: 'text-brand-400', bg: 'bg-brand-600/10 border-brand-600/20' },
  { label: 'Agent Performansı', desc: 'Çalışma süreleri, başarı oranları', icon: BarChart2, color: 'text-green-400', bg: 'bg-green-500/10 border-green-500/20' },
  { label: 'Müşteri Özeti', desc: 'Lead dönüşümü, takip istatistikleri', icon: Users, color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/20' },
  { label: 'İçerik Otomasyonu', desc: 'Yayınlanan içerik, platform dağılımı', icon: TrendingUp, color: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/20' },
]

export default function ReportsPage() {
  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in">
        <div>
          <h2 className="text-xl font-bold text-white">Raporlar</h2>
          <p className="text-sm text-gray-500 mt-1">Sistem geneli analitik ve istatistikler</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {cards.map(({ label, desc, icon: Icon, color, bg }) => (
            <div
              key={label}
              className={`flex items-start gap-4 p-5 bg-surface-50 border rounded-xl cursor-not-allowed opacity-60`}
            >
              <div className={`p-3 rounded-lg border ${bg} flex-shrink-0`}>
                <Icon size={20} className={color} />
              </div>
              <div>
                <p className="text-sm font-semibold text-white">{label}</p>
                <p className="text-xs text-gray-500 mt-0.5">{desc}</p>
                <span className="inline-block mt-2 text-xs text-gray-600 bg-surface-100 border border-surface-200 px-2 py-0.5 rounded-full">
                  Yakında
                </span>
              </div>
            </div>
          ))}
        </div>

        <div className="p-6 bg-surface-50 border border-surface-200 rounded-xl text-center">
          <BarChart2 size={32} className="text-gray-600 mx-auto mb-3" />
          <p className="text-sm font-medium text-gray-400">Raporlar modülü geliştirme aşamasında</p>
          <p className="text-xs text-gray-600 mt-1">Backend entegrasyonu tamamlandığında otomatik aktif olacak</p>
        </div>
      </div>
    </AppShell>
  )
}
