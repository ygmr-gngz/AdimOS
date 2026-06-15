'use client'

import { Mic, MicOff, Loader2, X } from 'lucide-react'
import { clsx } from 'clsx'
import type { VoiceState } from '@/types/voice'

interface VoiceCommandButtonProps {
  voiceState: VoiceState
  onStartRecording: () => void
  onStopRecording: () => void
  onStopPlayback: () => void
}

export default function VoiceCommandButton({
  voiceState,
  onStartRecording,
  onStopRecording,
  onStopPlayback,
}: VoiceCommandButtonProps) {
  const isRecording = voiceState === 'recording'
  const isProcessing = voiceState === 'processing'
  const isPlaying = voiceState === 'playing'
  const isIdle = voiceState === 'idle'

  const handleClick = () => {
    if (isRecording) onStopRecording()
    else if (isPlaying) onStopPlayback()
    else if (isIdle) onStartRecording()
  }

  return (
    <button
      onClick={handleClick}
      disabled={isProcessing}
      className={clsx(
        'relative w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 focus:outline-none',
        isRecording && 'bg-red-600 hover:bg-red-500 scale-110 shadow-lg shadow-red-600/40',
        isProcessing && 'bg-surface-100 cursor-not-allowed',
        isPlaying && 'bg-brand-600 hover:bg-brand-500 shadow-lg shadow-brand-600/40',
        isIdle && 'bg-brand-600 hover:bg-brand-500 hover:scale-105 shadow-lg shadow-brand-600/30',
      )}
    >
      {isRecording && (
        <span className="absolute inset-0 rounded-full bg-red-600 animate-ping opacity-30" />
      )}
      {isRecording ? (
        <MicOff size={32} className="text-white" />
      ) : isProcessing ? (
        <Loader2 size={32} className="text-gray-400 animate-spin" />
      ) : isPlaying ? (
        <X size={32} className="text-white" />
      ) : (
        <Mic size={32} className="text-white" />
      )}
    </button>
  )
}

export function VoiceStatusLabel({ voiceState }: { voiceState: VoiceState }) {
  const labels: Record<VoiceState, { text: string; color: string }> = {
    idle: { text: 'Konuşmak için tıklayın', color: 'text-gray-500' },
    recording: { text: 'Dinleniyor... (durdurmak için tıklayın)', color: 'text-red-400' },
    processing: { text: 'İşleniyor...', color: 'text-yellow-400' },
    playing: { text: 'Yanıt oynatılıyor... (durdurmak için tıklayın)', color: 'text-brand-400' },
    error: { text: 'Bir hata oluştu', color: 'text-red-400' },
  }
  const { text, color } = labels[voiceState]
  return <p className={clsx('text-sm font-medium animate-fade-in', color)}>{text}</p>
}
