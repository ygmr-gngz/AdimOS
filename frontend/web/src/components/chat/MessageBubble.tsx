import { Bot, User } from 'lucide-react'
import type { Message } from '@/types/chat'
import { clsx } from 'clsx'

interface MessageBubbleProps {
  message: Message
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  return (
    <div className={clsx('flex gap-3', isUser && 'flex-row-reverse')}>
      <div className={clsx('w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1',
        isUser ? 'bg-brand-600/30' : 'bg-surface-200'
      )}>
        {isUser ? <User size={15} className="text-brand-400" /> : <Bot size={15} className="text-gray-400" />}
      </div>
      <div className={clsx('max-w-[75%]', isUser && 'items-end flex flex-col')}>
        <div className={clsx(
          'px-4 py-3 rounded-2xl text-sm leading-relaxed',
          isUser
            ? 'bg-brand-600 text-white rounded-tr-sm'
            : 'bg-surface-100 text-gray-200 rounded-tl-sm'
        )}>
          {message.content}
        </div>
        {message.citations && message.citations.length > 0 && (
          <div className="mt-2 space-y-1">
            {message.citations.slice(0, 2).map((c, i) => (
              <div key={i} className="text-xs text-gray-600 bg-surface-50 border border-surface-200 rounded-lg px-3 py-1.5">
                <span className="text-gray-500">Kaynak: </span>
                <span className="text-gray-400">{c.document_name}</span>
              </div>
            ))}
          </div>
        )}
        <p className="text-xs text-gray-600 mt-1 px-1">
          {new Date(message.created_at).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </div>
  )
}
