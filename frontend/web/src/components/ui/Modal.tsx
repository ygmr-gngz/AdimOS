'use client'

import { Fragment } from 'react'
import { X } from 'lucide-react'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg'
}

const sizeClasses = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
}

export default function Modal({ isOpen, onClose, title, children, size = 'md' }: ModalProps) {
  if (!isOpen) return null

  return (
    <Fragment>
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
        onClick={onClose}
      />
      <div className={`fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full ${sizeClasses[size]} z-50 animate-fade-in`}>
        <div className="bg-surface-50 border border-surface-200 rounded-2xl shadow-2xl p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-semibold text-gray-100">{title}</h2>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-surface-100 text-gray-500 hover:text-gray-300 transition-colors"
            >
              <X size={18} />
            </button>
          </div>
          {children}
        </div>
      </div>
    </Fragment>
  )
}
