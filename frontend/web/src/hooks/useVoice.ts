'use client'

import { useState, useRef, useCallback } from 'react'
import { voiceService } from '@/services/voice.service'
import type { VoiceResponse, VoiceState } from '@/types/voice'
import toast from 'react-hot-toast'

export function useVoice() {
  const [voiceState, setVoiceState] = useState<VoiceState>('idle')
  const [transcript, setTranscript] = useState('')
  const [lastResponse, setLastResponse] = useState<VoiceResponse | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        setVoiceState('processing')
        try {
          const response = await voiceService.sendAudio(blob)
          setTranscript(response.transcript)
          setLastResponse(response)
          setVoiceState('playing')
          const audio = voiceService.playAudioBase64(response.answer_audio_base64)
          audioRef.current = audio
          audio.onended = () => setVoiceState('idle')
        } catch (err: unknown) {
          const msg = err instanceof Error ? err.message : JSON.stringify(err)
          toast.error(`Ses hatası: ${msg}`, { duration: 8000 })
          setVoiceState('error')
          setTimeout(() => setVoiceState('idle'), 2000)
        }
      }

      mediaRecorder.start()
      setVoiceState('recording')
    } catch {
      toast.error('Mikrofon erişimi reddedildi')
      setVoiceState('error')
      setTimeout(() => setVoiceState('idle'), 2000)
    }
  }, [])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && voiceState === 'recording') {
      mediaRecorderRef.current.stop()
    }
  }, [voiceState])

  const stopPlayback = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
      setVoiceState('idle')
    }
  }, [])

  return { voiceState, transcript, lastResponse, startRecording, stopRecording, stopPlayback }
}
