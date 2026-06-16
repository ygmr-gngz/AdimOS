export type MessageRole = 'user' | 'assistant' | 'system'

export interface ChatSource {
  document_id: string
  filename: string
  content_preview: string
  similarity: number
}

export interface Message {
  id: string
  role: MessageRole
  content: string
  created_at: string
  sources?: ChatSource[]
  used_rag?: boolean
}

export interface ChatRequest {
  message: string
  conversation_id?: string
}

export interface ChatResponse {
  success: boolean
  answer: string
  sources: ChatSource[]
  used_rag: boolean
  conversation_id: string | null
}

export interface Conversation {
  id: string
  title: string
  created_at: string
  updated_at: string
}
