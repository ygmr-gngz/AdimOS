import { HTMLAttributes, forwardRef } from 'react'
import { clsx } from 'clsx'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'bordered' | 'elevated'
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ variant = 'default', className, children, ...props }, ref) => {
    const variants = {
      default: 'bg-surface-50 rounded-xl p-5',
      bordered: 'bg-surface-50 rounded-xl p-5 border border-surface-200',
      elevated: 'bg-surface-50 rounded-xl p-5 shadow-lg shadow-black/30',
    }
    return (
      <div ref={ref} className={clsx(variants[variant], className)} {...props}>
        {children}
      </div>
    )
  }
)

Card.displayName = 'Card'

export function CardHeader({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={clsx('mb-4', className)} {...props}>
      {children}
    </div>
  )
}

export function CardTitle({ className, children, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={clsx('text-base font-semibold text-gray-100', className)} {...props}>
      {children}
    </h3>
  )
}

export default Card
