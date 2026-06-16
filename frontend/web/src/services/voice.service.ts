import apiClient from '@/lib/api-client'
import type { VoiceResponse } from '@/types/voice'

export const voiceService = {
  async sendAudio(audioBlob: Blob): Promise<VoiceResponse> {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'audio.webm')
    const { data } = await apiClient.post('/voice', formData)
    return data
  },

  playAudioBase64(base64: string): HTMLAudioElement {
    const audio = new Audio(`data:audio/mp3;base64,${base64}`)
    audio.play()
    return audio
  },
}
