import { Bot, User, FileText, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import type { Message } from '@/types/chat'
import { clsx } from 'clsx'

interface MessageBubbleProps {
  message: Message
}

function SimilarityBar({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  const color = value >= 0.7 ? 'bg-green-500' : value >= 0.5 ? 'bg-yellow-500' : 'bg-orange-500'
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-16 h-1 bg-surface-200 rounded-full overflow-hidden">
        <div className={clsx('h-full rounded-full', color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-600">{pct}%</span>
    </div>
  )
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const hasSources = !isUser && message.sources && message.sources.length > 0
  const [sourcesOpen, setSourcesOpen] = useState(false)

  return (
    <div className={clsx('flex gap-3', isUser && 'flex-row-reverse')}>
      <div className={clsx(
        'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1',
        isUser ? 'bg-brand-600/30' : 'bg-surface-200'
      )}>
        {isUser
          ? <User size={15} className="text-brand-400" />
          : <Bot size={15} className="text-gray-400" />}
      </div>

      <div className={clsx('max-w-[78%]', isUser && 'items-end flex flex-col')}>
        <div className={clsx(
          'px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap',
          isUser
            ? 'bg-brand-600 text-white rounded-tr-sm'
            : 'bg-surface-100 text-gray-200 rounded-tl-sm'
        )}>
          {message.content}
        </div>

        {hasSources && (
          <div className="mt-2 w-full">
            <button
              onClick={() => setSourcesOpen(!sourcesOpen)}
              className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-300 transition-colors"
            >
              <FileText size={11} />
              {message.sources!.length} kaynak kullanıldı
              {sourcesOpen ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
              {message.used_rag && (
                <span className="ml-1 px-1.5 py-0.5 bg-brand-600/20 text-brand-400 rounded text-xs">RAG</span>
              )}
            </button>

            {sourcesOpen && (
              <div className="mt-1.5 space-y-1.5">
                {message.sources!.map((src, i) => (
                  <div
                    key={i}
                    className="bg-surface-50 border border-surface-200 rounded-lg px-3 py-2"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-gray-400 truncate max-w-[200px]">
                        {src.filename}
                      </span>
                      <SimilarityBar value={src.similarity} />
                    </div>
                    <p className="text-xs text-gray-600 line-clamp-2">{src.content_preview}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <p className="text-xs text-gray-600 mt-1 px-1">
          {new Date(message.created_at).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </div>
  )
}
