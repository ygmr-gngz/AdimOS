'use client'

import { Suspense, useState, useRef, useEffect, useCallback } from 'react'
import { useSearchParams } from 'next/navigation'
import { Mic, MicOff, Send, Paperclip, X, Bot, Loader2, FileText, Sheet } from 'lucide-react'
import { clsx } from 'clsx'
import toast, { Toaster } from 'react-hot-toast'
import { widgetService } from '@/services/widget.service'

type MsgRole = 'visitor' | 'assistant'
type VoiceState = 'idle' | 'recording' | 'processing'

interface PendingFile {
  id: string
  file: File
  kind: 'pdf' | 'excel' | 'csv' | 'other'
}

interface Msg {
  id: string
  role: MsgRole
  content: string
  inputType?: 'text' | 'voice' | 'file'
  files?: { name: string; kind: string; size: number }[]
}

function fileKind(file: File): PendingFile['kind'] {
  if (file.type === 'application/pdf') return 'pdf'
  if (file.name.match(/\.xlsx?$/i) || file.type.includes('spreadsheet') || file.type.includes('excel')) return 'excel'
  if (file.name.match(/\.csv$/i) || file.type === 'text/csv') return 'csv'
  return 'other'
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function FileIcon({ kind, size = 14 }: { kind: string; size?: number }) {
  if (kind === 'pdf') return <FileText size={size} className="text-red-400" />
  if (kind === 'excel' || kind === 'csv') return <Sheet size={size} className="text-green-400" />
  return <FileText size={size} className="text-gray-400" />
}

function WidgetChat() {
  const params = useSearchParams()
  const siteId = params.get('siteId') || 'default'
  const title = params.get('title') || 'Adım Asistanı'

  const [messages, setMessages] = useState<Msg[]>([])
  const [inputText, setInputText] = useState('')
  const [pendingFiles, setPendingFiles] = useState<PendingFile[]>([])
  const [isSending, setIsSending] = useState(false)
  const [voiceState, setVoiceState] = useState<VoiceState>('idle')
  const [conversationId, setConversationId] = useState<string | undefined>()

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Visitor ID — sessionStorage
  const visitorId = useRef<string>('')
  useEffect(() => {
    const key = `adimos_visitor_${siteId}`
    let id = sessionStorage.getItem(key)
    if (!id) {
      id = `v_${Date.now()}_${Math.random().toString(36).slice(2)}`
      sessionStorage.setItem(key, id)
    }
    visitorId.current = id
    const savedConv = sessionStorage.getItem(`adimos_conv_${siteId}`)
    if (savedConv) setConversationId(savedConv)
  }, [siteId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const addMsg = useCallback((role: MsgRole, content: string, extras?: Partial<Msg>) => {
    setMessages(prev => [...prev, {
      id: `${Date.now()}-${Math.random()}`,
      role,
      content,
      ...extras,
    }])
  }, [])

  const handleSend = useCallback(async () => {
    const content = inputText.trim()
    const files = pendingFiles.map(p => p.file)
    if (!content && files.length === 0) return
    if (isSending) return

    const userMsgFiles = pendingFiles.map(p => ({ name: p.file.name, kind: p.kind, size: p.file.size }))
    addMsg('visitor', content || '📎 Dosya gönderildi', {
      inputType: files.length > 0 ? 'file' : 'text',
      files: userMsgFiles.length > 0 ? userMsgFiles : undefined,
    })
    setInputText('')
    setPendingFiles([])
    setIsSending(true)

    try {
      const res = await widgetService.sendMessage({
        site_id: siteId,
        message: content || undefined,
        files: files.length > 0 ? files : undefined,
        conversation_id: conversationId,
        visitor_id: visitorId.current,
      })
      if (res.conversation_id) {
        setConversationId(res.conversation_id)
        sessionStorage.setItem(`adimos_conv_${siteId}`, res.conversation_id)
      }
      addMsg('assistant', res.answer)
    } catch {
      toast.error('Mesaj gönderilemedi')
    } finally {
      setIsSending(false)
    }
  }, [inputText, pendingFiles, isSending, siteId, conversationId, addMsg])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files || [])
    const allowed = selected.filter(f => {
      const kind = fileKind(f)
      return kind !== 'other' || f.size < 20 * 1024 * 1024
    })
    setPendingFiles(prev => [
      ...prev,
      ...allowed.map(f => ({ id: `${Date.now()}-${Math.random()}`, file: f, kind: fileKind(f) })),
    ])
    e.target.value = ''
  }, [])

  const handleStartVoice = useCallback(async () => {
    if (voiceState !== 'idle') return
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mr = new MediaRecorder(stream)
      mediaRecorderRef.current = mr
      chunksRef.current = []
      mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      mr.onstop = async () => {
        stream.getTracks().forEach(t => t.stop())
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        setVoiceState('processing')
        try {
          const res = await widgetService.sendVoice({
            site_id: siteId,
            audio: blob,
            conversation_id: conversationId,
            visitor_id: visitorId.current,
          })
          if (res.conversation_id) {
            setConversationId(res.conversation_id)
            sessionStorage.setItem(`adimos_conv_${siteId}`, res.conversation_id)
          }
          addMsg('visitor', res.transcript, { inputType: 'voice' })
          addMsg('assistant', res.answer)
          if (res.answer_audio_base64) {
            const audio = new Audio(`data:audio/mpeg;base64,${res.answer_audio_base64}`)
            audio.play().catch(() => {})
          }
        } catch {
          toast.error('Ses işlenemedi')
        } finally {
          setVoiceState('idle')
        }
      }
      mr.start()
      setVoiceState('recording')
    } catch {
      toast.error('Mikrofon erişimi reddedildi')
    }
  }, [voiceState, siteId, conversationId, addMsg])

  const handleStopVoice = useCallback(() => {
    if (mediaRecorderRef.current && voiceState === 'recording') {
      mediaRecorderRef.current.stop()
    }
  }, [voiceState])

  const isBusy = isSending || voiceState !== 'idle'

  const suggestions = [
    'Hizmetleriniz hakkında bilgi alabilir miyim?',
    'SGS sınavı başvuru şartları nelerdir?',
    'Randevu almak istiyorum',
  ]

  return (
    <div className="flex flex-col h-screen bg-[#0f0f14] text-white">
      <Toaster position="top-center" toastOptions={{ style: { background: '#1a1a24', color: '#fff', border: '1px solid #2c2c3d' } }} />

      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-[#2c2c3d] bg-[#1a1a24] flex-shrink-0">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#3b5bdb] to-[#7048e8] flex items-center justify-center flex-shrink-0">
          <Bot size={15} className="text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-white truncate">{title}</p>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            <span className="text-xs text-gray-500">Çevrimiçi</span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center gap-4 px-4">
            <div className="w-14 h-14 rounded-full bg-gradient-to-br from-[#3b5bdb]/20 to-[#7048e8]/20 border border-[#3b5bdb]/20 flex items-center justify-center">
              <Bot size={26} className="text-[#748ffc]" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white">Merhaba! 👋</p>
              <p className="text-xs text-gray-500 mt-1 leading-relaxed">
                Size nasıl yardımcı olabilirim?<br />
                Yazın, sesle sorun ya da dosya yükleyin.
              </p>
            </div>
            <div className="w-full space-y-1.5 mt-2">
              {suggestions.map(s => (
                <button
                  key={s}
                  onClick={() => { setInputText(s); inputRef.current?.focus() }}
                  className="w-full text-left text-xs text-gray-400 bg-[#1a1a24] hover:bg-[#22222f] border border-[#2c2c3d] rounded-xl px-3 py-2.5 transition-colors hover:text-gray-200"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map(msg => (
            <div key={msg.id} className={clsx('flex gap-2', msg.role === 'visitor' ? 'flex-row-reverse' : '')}>
              {msg.role === 'assistant' && (
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#3b5bdb] to-[#7048e8] flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Bot size={12} className="text-white" />
                </div>
              )}
              <div className={clsx(
                'max-w-[80%] space-y-1.5',
                msg.role === 'visitor' ? 'items-end' : 'items-start',
              )}>
                {msg.files && msg.files.length > 0 && (
                  <div className="space-y-1">
                    {msg.files.map((f, i) => (
                      <div key={i} className="flex items-center gap-2 bg-[#22222f] border border-[#2c2c3d] rounded-xl px-3 py-2">
                        <FileIcon kind={f.kind} />
                        <div className="min-w-0">
                          <p className="text-xs text-gray-200 truncate max-w-[160px]">{f.name}</p>
                          <p className="text-[10px] text-gray-500">{formatSize(f.size)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {msg.content && msg.content !== '📎 Dosya gönderildi' && (
                  <div className={clsx(
                    'px-3 py-2 rounded-2xl text-sm leading-relaxed',
                    msg.role === 'visitor'
                      ? 'bg-[#3b5bdb] text-white rounded-tr-sm'
                      : 'bg-[#1a1a24] text-gray-200 rounded-tl-sm border border-[#2c2c3d]'
                  )}>
                    {msg.inputType === 'voice' && msg.role === 'visitor' && (
                      <div className="flex items-center gap-1 mb-1 opacity-70">
                        <Mic size={9} />
                        <span className="text-[10px]">sesli</span>
                      </div>
                    )}
                    {msg.content}
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {(isSending || voiceState === 'processing') && (
          <div className="flex gap-2">
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#3b5bdb] to-[#7048e8] flex items-center justify-center flex-shrink-0">
              <Bot size={12} className="text-white" />
            </div>
            <div className="bg-[#1a1a24] border border-[#2c2c3d] rounded-2xl rounded-tl-sm px-3 py-2.5">
              <div className="flex gap-1.5 items-center">
                {[0, 150, 300].map(d => (
                  <div key={d} className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce" style={{ animationDelay: `${d}ms` }} />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Pending files */}
      {pendingFiles.length > 0 && (
        <div className="px-3 pb-1 flex flex-wrap gap-1.5 flex-shrink-0">
          {pendingFiles.map(pf => (
            <div key={pf.id} className="flex items-center gap-1.5 bg-[#22222f] border border-[#2c2c3d] rounded-lg px-2 py-1">
              <FileIcon kind={pf.kind} size={12} />
              <span className="text-xs text-gray-300 max-w-[120px] truncate">{pf.file.name}</span>
              <button onClick={() => setPendingFiles(p => p.filter(x => x.id !== pf.id))}>
                <X size={11} className="text-gray-500 hover:text-gray-300" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="flex-shrink-0 p-3 border-t border-[#2c2c3d] bg-[#1a1a24]">
        {voiceState === 'recording' && (
          <div className="flex items-center gap-2 mb-2 py-1.5 px-3 bg-red-500/10 border border-red-500/20 rounded-xl">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
            <span className="text-xs text-red-400">Kaydediliyor — durdurmak için tıklayın</span>
          </div>
        )}
        <div className="flex items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.xlsx,.xls,.csv"
            multiple
            className="hidden"
            onChange={handleFileSelect}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isBusy}
            title="Dosya ekle (PDF, Excel, CSV)"
            className="w-9 h-9 rounded-xl flex items-center justify-center bg-[#22222f] border border-[#2c2c3d] text-gray-400 hover:text-gray-200 hover:border-[#3c3c4d] disabled:opacity-40 transition-colors flex-shrink-0"
          >
            <Paperclip size={15} />
          </button>
          <input
            ref={inputRef}
            value={inputText}
            onChange={e => setInputText(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
            placeholder="Mesajınızı yazın..."
            disabled={isBusy}
            className="flex-1 bg-[#22222f] border border-[#2c2c3d] text-sm text-gray-200 placeholder-gray-600 rounded-xl px-3 py-2 outline-none focus:border-[#3b5bdb]/50 disabled:opacity-50 transition-colors"
          />
          <button
            onClick={voiceState === 'recording' ? handleStopVoice : handleStartVoice}
            disabled={isSending || voiceState === 'processing'}
            aria-label="Sesle sor"
            className={clsx(
              'w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 transition-all',
              voiceState === 'recording'
                ? 'bg-red-500 text-white'
                : 'bg-[#22222f] border border-[#2c2c3d] text-gray-400 hover:text-gray-200 hover:border-[#3c3c4d] disabled:opacity-40'
            )}
          >
            {voiceState === 'processing'
              ? <Loader2 size={14} className="animate-spin" />
              : voiceState === 'recording'
              ? <MicOff size={14} />
              : <Mic size={14} />
            }
          </button>
          <button
            onClick={handleSend}
            disabled={(!inputText.trim() && pendingFiles.length === 0) || isBusy}
            aria-label="Gönder"
            className="w-9 h-9 rounded-xl bg-[#3b5bdb] hover:bg-[#4c6ef5] disabled:opacity-40 disabled:cursor-not-allowed text-white flex items-center justify-center flex-shrink-0 transition-colors"
          >
            {isSending ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
          </button>
        </div>
        <p className="text-center text-[10px] text-gray-700 mt-2">AdimOS · AI Asistan</p>
      </div>
    </div>
  )
}

export default function WidgetPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-screen bg-[#0f0f14]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#3b5bdb] to-[#7048e8] animate-pulse" />
          <p className="text-xs text-gray-500">Yükleniyor...</p>
        </div>
      </div>
    }>
      <WidgetChat />
    </Suspense>
  )
}
