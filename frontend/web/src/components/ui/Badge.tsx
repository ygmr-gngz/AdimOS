import { HTMLAttributes } from 'react'
import { clsx } from 'clsx'

type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info' | 'purple'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
  dot?: boolean
}

const variantClasses: Record<BadgeVariant, string> = {
  default: 'bg-surface-200 text-gray-300',
  success: 'bg-green-500/20 text-green-400',
  warning: 'bg-yellow-500/20 text-yellow-400',
  error: 'bg-red-500/20 text-red-400',
  info: 'bg-blue-500/20 text-blue-400',
  purple: 'bg-purple-500/20 text-purple-400',
}

const dotClasses: Record<BadgeVariant, string> = {
  default: 'bg-gray-400',
  success: 'bg-green-400',
  warning: 'bg-yellow-400',
  error: 'bg-red-400',
  info: 'bg-blue-400',
  purple: 'bg-purple-400',
}

export default function Badge({ variant = 'default', dot, className, children, ...props }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium',
        variantClasses[variant],
        className
      )}
      {...props}
    >
      {dot && (
        <span className={clsx('w-1.5 h-1.5 rounded-full', dotClasses[variant])} />
      )}
      {children}
    </span>
  )
}
