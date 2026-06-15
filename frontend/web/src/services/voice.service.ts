import apiClient from '@/lib/api-client'
import type { VoiceResponse } from '@/types/voice'

export const voiceService = {
  async sendAudio(audioBlob: Blob): Promise<VoiceResponse> {
    const arrayBuffer = await audioBlob.arrayBuffer()
    const base64 = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)))
    const { data } = await apiClient.post('/voice', {
      audio_base64: base64,
      format: 'webm',
    })
    return data
  },

  playAudioBase64(base64: string): HTMLAudioElement {
    const audio = new Audio(`data:audio/mp3;base64,${base64}`)
    audio.play()
    return audio
  },
}
