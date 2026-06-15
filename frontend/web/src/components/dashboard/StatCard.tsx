import { LucideIcon } from 'lucide-react'
import { clsx } from 'clsx'

interface StatCardProps {
  label: string
  value: number | string
  icon: LucideIcon
  color?: 'blue' | 'green' | 'purple' | 'orange' | 'red'
  trend?: { value: number; label: string }
}

const colorClasses = {
  blue: { bg: 'bg-blue-500/15', icon: 'text-blue-400', border: 'border-blue-500/20' },
  green: { bg: 'bg-green-500/15', icon: 'text-green-400', border: 'border-green-500/20' },
  purple: { bg: 'bg-purple-500/15', icon: 'text-purple-400', border: 'border-purple-500/20' },
  orange: { bg: 'bg-orange-500/15', icon: 'text-orange-400', border: 'border-orange-500/20' },
  red: { bg: 'bg-red-500/15', icon: 'text-red-400', border: 'border-red-500/20' },
}

export default function StatCard({ label, value, icon: Icon, color = 'blue', trend }: StatCardProps) {
  const c = colorClasses[color]
  return (
    <div className={clsx('bg-surface-50 rounded-xl p-5 border', c.border)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">{label}</p>
          <p className="text-3xl font-bold text-white mt-1">{value}</p>
          {trend && (
            <p className="text-xs text-gray-500 mt-1">
              <span className={trend.value >= 0 ? 'text-green-400' : 'text-red-400'}>
                {trend.value >= 0 ? '+' : ''}{trend.value}%
              </span>
              {' '}{trend.label}
            </p>
          )}
        </div>
        <div className={clsx('p-2.5 rounded-lg', c.bg)}>
          <Icon size={20} className={c.icon} />
        </div>
      </div>
    </div>
  )
}
