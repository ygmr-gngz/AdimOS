'use client'

import AppShell from '@/components/layout/AppShell'
import VoiceCommandButton, { VoiceStatusLabel } from '@/components/voice/VoiceCommandButton'
import { useVoice } from '@/hooks/useVoice'
import { Bot, Mic } from 'lucide-react'

export default function VoicePage() {
  const { voiceState, transcript, lastResponse, startRecording, stopRecording, stopPlayback } = useVoice()

  return (
    <AppShell>
      <div className="flex flex-col items-center justify-center animate-fade-in py-10">
        <div className="text-center mb-12">
          <h2 className="text-xl font-bold text-white mb-2">Sesli Asistan</h2>
          <p className="text-sm text-gray-500 max-w-md">
            Mikrofona basın, sorunuzu sorun — AI sesli olarak yanıtlayacak
          </p>
        </div>

        <div className="relative flex flex-col items-center gap-6">
          <VoiceCommandButton
            voiceState={voiceState}
            onStartRecording={startRecording}
            onStopRecording={stopRecording}
            onStopPlayback={stopPlayback}
          />
          <VoiceStatusLabel voiceState={voiceState} />
        </div>

        {transcript && (
          <div className="mt-10 w-full max-w-xl space-y-4">
            <div className="bg-surface-50 border border-surface-200 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <Mic size={13} className="text-gray-500" />
                <span className="text-xs font-medium text-gray-500">Siz</span>
              </div>
              <p className="text-sm text-gray-300">{transcript}</p>
            </div>

            {lastResponse && (
              <div className="bg-brand-950/60 border border-brand-600/20 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Bot size={13} className="text-brand-400" />
                  <span className="text-xs font-medium text-brand-400">AdimOS</span>
                  <span className="ml-auto text-xs text-gray-600">{lastResponse.agent_used}</span>
                </div>
                <p className="text-sm text-gray-300 leading-relaxed">{lastResponse.answer_text}</p>
              </div>
            )}
          </div>
        )}

        <div className="mt-12 grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-xl">
          {[
            'Bugün hangi eğitimlerim var?',
            'Son yüklenen dokümanı özetle',
            'Kaç aktif müşterim var?',
            'Günlük özetimi oluştur',
          ].map((hint) => (
            <button
              key={hint}
              onClick={startRecording}
              className="text-xs text-gray-500 bg-surface-50 border border-surface-200 rounded-lg px-3 py-2.5 hover:text-gray-300 hover:border-surface-300 transition-colors text-left"
            >
              &ldquo;{hint}&rdquo;
            </button>
          ))}
        </div>
      </div>
    </AppShell>
  )
}
