'use client'

import { useState, useCallback } from 'react'
import { chatService } from '@/services/chat.service'
import type { Message, Citation } from '@/types/chat'
import toast from 'react-hot-toast'

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | undefined>()

  const sendMessage = useCallback(async (content: string) => {
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])
    setIsLoading(true)
    try {
      const response = await chatService.sendMessage({
        message: content,
        conversation_id: conversationId,
      })
      if (response.conversation_id) setConversationId(response.conversation_id)
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        created_at: new Date().toISOString(),
        citations: response.citations as Citation[],
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch {
      toast.error('Mesaj gönderilemedi')
      setMessages((prev) => prev.slice(0, -1))
    } finally {
      setIsLoading(false)
    }
  }, [conversationId])

  const clearChat = useCallback(() => {
    setMessages([])
    setConversationId(undefined)
  }, [])

  return { messages, isLoading, sendMessage, clearChat }
}
