'use client'

import { useState, useCallback, useEffect } from 'react'
import { chatService } from '@/services/chat.service'
import type { Message, Conversation } from '@/types/chat'
import toast from 'react-hot-toast'

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string | undefined>()
  const [isLoading, setIsLoading] = useState(false)
  const [isHistoryLoading, setIsHistoryLoading] = useState(false)

  // Load conversation list on mount
  useEffect(() => {
    chatService.getConversations()
      .then(setConversations)
      .catch(() => {})
  }, [])

  const loadConversation = useCallback(async (conversationId: string) => {
    setIsHistoryLoading(true)
    setActiveConversationId(conversationId)
    try {
      const msgs = await chatService.getMessages(conversationId)
      setMessages(msgs)
    } catch {
      toast.error('Sohbet yüklenemedi')
    } finally {
      setIsHistoryLoading(false)
    }
  }, [])

  const startNewChat = useCallback(() => {
    setMessages([])
    setActiveConversationId(undefined)
  }, [])

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
        conversation_id: activeConversationId,
      })

      if (response.conversation_id && !activeConversationId) {
        setActiveConversationId(response.conversation_id)
        // Add to conversations list
        chatService.getConversations().then(setConversations).catch(() => {})
      }

      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        created_at: new Date().toISOString(),
        sources: response.sources,
        used_rag: response.used_rag,
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch {
      toast.error('Mesaj gönderilemedi')
      setMessages((prev) => prev.slice(0, -1))
    } finally {
      setIsLoading(false)
    }
  }, [activeConversationId])

  const deleteConversation = useCallback(async (conversationId: string) => {
    try {
      await chatService.deleteConversation(conversationId)
      setConversations((prev) => prev.filter((c) => c.id !== conversationId))
      if (activeConversationId === conversationId) {
        startNewChat()
      }
    } catch {
      toast.error('Sohbet silinemedi')
    }
  }, [activeConversationId, startNewChat])

  return {
    messages,
    conversations,
    activeConversationId,
    isLoading,
    isHistoryLoading,
    sendMessage,
    loadConversation,
    startNewChat,
    deleteConversation,
  }
}
