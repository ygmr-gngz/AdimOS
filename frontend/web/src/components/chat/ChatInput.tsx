'use client'

import { useState, KeyboardEvent } from 'react'
import { Send } from 'lucide-react'

interface ChatInputProps {
  onSend: (message: string) => void
  isLoading: boolean
}

export default function ChatInput({ onSend, isLoading }: ChatInputProps) {
  const [value, setValue] = useState('')

  const handleSend = () => {
    const trimmed = value.trim()
    if (!trimmed || isLoading) return
    onSend(trimmed)
    setValue('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex gap-3 items-end">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Sorunuzu yazın... (Enter: gönder, Shift+Enter: yeni satır)"
        rows={1}
        className="flex-1 bg-surface-100 border border-surface-200 rounded-xl px-4 py-3 text-sm text-gray-100 placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-colors"
        style={{ maxHeight: '120px' }}
      />
      <button
        onClick={handleSend}
        disabled={!value.trim() || isLoading}
        className="p-3 bg-brand-600 hover:bg-brand-500 text-white rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
      >
        <Send size={18} />
      </button>
    </div>
  )
}
