'use client'

import AppShell from '@/components/layout/AppShell'
import { GraduationCap, Users, BookOpen, TrendingUp } from 'lucide-react'
import Badge from '@/components/ui/Badge'

export default function AcademyPage() {
  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in">
        <div>
          <h2 className="text-xl font-bold text-white mb-1">SGS Academy</h2>
          <p className="text-sm text-gray-500">Öğrenci takibi ve AI destekli öğrenme planı</p>
        </div>

        <div className="grid grid-cols-3 gap-4">
          {[
            { label: 'Aktif Öğrenci', value: '0', icon: Users },
            { label: 'Tamamlanan Soru', value: '0', icon: BookOpen },
            { label: 'Ort. Başarı', value: '—', icon: TrendingUp },
          ].map((s) => (
            <div key={s.label} className="bg-surface-50 rounded-xl p-5 border border-surface-200">
              <s.icon size={18} className="text-gray-500 mb-2" />
              <p className="text-2xl font-bold text-white">{s.value}</p>
              <p className="text-xs text-gray-500 mt-1">{s.label}</p>
            </div>
          ))}
        </div>

        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="p-4 bg-surface-100 rounded-2xl mb-4">
            <GraduationCap size={40} className="text-gray-500" />
          </div>
          <p className="text-sm font-medium text-gray-400 mb-1">SGS Academy modülü hazırlanıyor</p>
          <p className="text-xs text-gray-600 max-w-xs">
            Öğrenci kaydı, soru bankası, analiz ve AI öğrenme planı özellikleri yakında aktif olacak
          </p>
          <Badge variant="warning" className="mt-4">Faz 3</Badge>
        </div>
      </div>
    </AppShell>
  )
}
