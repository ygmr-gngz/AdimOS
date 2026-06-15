'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { X, Mic, MicOff, Send, Bot, Loader2 } from 'lucide-react'
import { clsx } from 'clsx'
import { chatService } from '@/services/chat.service'
import { voiceService } from '@/services/voice.service'
import toast from 'react-hot-toast'

type Msg = {
  id: string
  role: 'user' | 'assistant'
  content: string
  inputType?: 'text' | 'voice'
}

interface Props {
  isOpen: boolean
  onOpen: () => void
  onClose: () => void
}

export default function AssistantWidget({ isOpen, onOpen, onClose }: Props) {
  const [messages, setMessages] = useState<Msg[]>([])
  const [inputText, setInputText] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [voiceState, setVoiceState] = useState<'idle' | 'recording' | 'processing'>('idle')
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isOpen) setTimeout(() => inputRef.current?.focus(), 120)
  }, [isOpen])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const addMsg = useCallback((role: 'user' | 'assistant', content: string, inputType?: 'text' | 'voice') => {
    setMessages(prev => [...prev, { id: `${Date.now()}-${Math.random()}`, role, content, inputType }])
  }, [])

  const handleSendText = useCallback(async () => {
    const content = inputText.trim()
    if (!content || isSending) return
    setInputText('')
    addMsg('user', content, 'text')
    setIsSending(true)
    try {
      const res = await chatService.sendMessage({ message: content })
      addMsg('assistant', res.answer)
    } catch {
      toast.error('Mesaj gönderilemedi')
    } finally {
      setIsSending(false)
    }
  }, [inputText, isSending, addMsg])

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
          const res = await voiceService.sendAudio(blob)
          addMsg('user', res.transcript, 'voice')
          addMsg('assistant', res.answer_text, 'voice')
          if (res.answer_audio_base64) {
            const audio = voiceService.playAudioBase64(res.answer_audio_base64)
            audioRef.current = audio
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
  }, [voiceState, addMsg])

  const handleStopVoice = useCallback(() => {
    if (mediaRecorderRef.current && voiceState === 'recording') {
      mediaRecorderRef.current.stop()
    }
  }, [voiceState])

  const isBusy = isSending || voiceState !== 'idle'

  return (
    <>
      {/* Floating button */}
      <div className="fixed bottom-6 right-6 z-40 flex items-center gap-3">
        {!isOpen && (
          <span className="text-sm text-gray-400 bg-surface-50/90 backdrop-blur border border-surface-200 px-3 py-1.5 rounded-full select-none">
            AdimOS ile konuş
          </span>
        )}
        <button
          onClick={isOpen ? onClose : onOpen}
          aria-label={isOpen ? 'Asistanı kapat' : 'Asistanı aç'}
          className={clsx(
            'w-14 h-14 rounded-full flex items-center justify-center shadow-lg transition-all duration-200',
            isOpen
              ? 'bg-surface-100 border border-surface-200 text-gray-400 hover:text-gray-200'
              : 'bg-gradient-to-br from-brand-500 to-brand-700 text-white hover:shadow-[0_0_32px_rgba(99,102,241,0.5)]'
          )}
        >
          {isOpen ? <X size={20} /> : <Mic size={22} />}
        </button>
      </div>

      {/* Panel */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-[380px] h-[540px] z-40 flex flex-col bg-surface-50 border border-surface-200 rounded-2xl shadow-2xl overflow-hidden animate-slide-in">
          {/* Panel header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-surface-200 flex-shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center">
                <Bot size={13} className="text-white" />
              </div>
              <div>
                <p className="text-sm font-semibold text-white">AdimOS Asistan</p>
                <p className="text-xs text-gray-500">Yazın veya sesle sorun</p>
              </div>
            </div>
            {messages.length > 0 && (
              <button
                onClick={() => setMessages([])}
                className="text-xs text-gray-600 hover:text-gray-400 transition-colors"
              >
                Temizle
              </button>
            )}
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center gap-3">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-brand-500/20 to-brand-700/20 border border-brand-600/20 flex items-center justify-center">
                  <Bot size={22} className="text-brand-400" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-300">Size nasıl yardımcı olabilirim?</p>
                  <p className="text-xs text-gray-500 mt-1">Yazın ya da mikrofona basarak sesle sorun</p>
                </div>
                <div className="grid grid-cols-1 gap-1.5 w-full mt-2">
                  {[
                    'Bugün hangi görevlerim var?',
                    'Son dokümanı özetle',
                    'Aktif müşterilerimi listele',
                  ].map(q => (
                    <button
                      key={q}
                      onClick={() => { setInputText(q); inputRef.current?.focus() }}
                      className="text-left text-xs text-gray-400 bg-surface-100 hover:bg-surface-200 border border-surface-200 rounded-lg px-3 py-2 transition-colors hover:text-gray-200"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map(msg => (
                <div
                  key={msg.id}
                  className={clsx('flex gap-2', msg.role === 'user' ? 'flex-row-reverse' : '')}
                >
                  {msg.role === 'assistant' && (
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Bot size={11} className="text-white" />
                    </div>
                  )}
                  <div
                    className={clsx(
                      'max-w-[78%] px-3 py-2 rounded-2xl text-sm leading-relaxed',
                      msg.role === 'user'
                        ? 'bg-brand-600 text-white rounded-tr-sm'
                        : 'bg-surface-100 text-gray-200 rounded-tl-sm'
                    )}
                  >
                    {msg.inputType === 'voice' && msg.role === 'user' && (
                      <div className="flex items-center gap-1.5 mb-1">
                        <Mic size={10} className="text-brand-200" />
                        <span className="text-[10px] text-brand-200">sesli</span>
                      </div>
                    )}
                    {msg.content}
                  </div>
                </div>
              ))
            )}

            {(isSending || voiceState === 'processing') && (
              <div className="flex gap-2">
                <div className="w-6 h-6 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center flex-shrink-0">
                  <Bot size={11} className="text-white" />
                </div>
                <div className="bg-surface-100 rounded-2xl rounded-tl-sm px-3 py-2.5">
                  <div className="flex gap-1.5 items-center">
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="flex-shrink-0 p-3 border-t border-surface-200">
            {voiceState === 'recording' && (
              <div className="flex items-center gap-2 mb-2 py-1.5 px-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                <span className="text-xs text-red-400">Kaydediliyor — durdurmak için tıklayın</span>
              </div>
            )}
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                value={inputText}
                onChange={e => setInputText(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendText() } }}
                placeholder="Bir şeyler yazın..."
                disabled={isBusy}
                className="flex-1 bg-surface-100 border border-surface-200 text-sm text-gray-200 placeholder-gray-600 rounded-xl px-3 py-2.5 outline-none focus:border-brand-600/50 disabled:opacity-50 transition-colors"
              />
              <button
                onClick={voiceState === 'recording' ? handleStopVoice : handleStartVoice}
                disabled={isSending || voiceState === 'processing'}
                aria-label="Sesle sor"
                className={clsx(
                  'w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-all',
                  voiceState === 'recording'
                    ? 'bg-red-500 text-white'
                    : 'bg-surface-100 border border-surface-200 text-gray-400 hover:text-gray-200 hover:border-surface-300 disabled:opacity-40'
                )}
              >
                {voiceState === 'processing'
                  ? <Loader2 size={15} className="animate-spin" />
                  : voiceState === 'recording'
                  ? <MicOff size={15} />
                  : <Mic size={15} />
                }
              </button>
              <button
                onClick={handleSendText}
                disabled={!inputText.trim() || isBusy}
                aria-label="Gönder"
                className="w-10 h-10 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-40 disabled:cursor-not-allowed text-white flex items-center justify-center flex-shrink-0 transition-colors"
              >
                {isSending ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
