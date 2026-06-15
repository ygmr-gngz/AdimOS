export type MessageRole = 'user' | 'assistant' | 'system'

export interface Message {
  id: string
  role: MessageRole
  content: string
  created_at: string
  citations?: Citation[]
}

export interface Citation {
  document_id: string
  document_name: string
  chunk_content: string
  similarity_score: number
}

export interface ChatRequest {
  message: string
  conversation_id?: string
}

export interface ChatResponse {
  answer: string
  citations: Citation[]
  conversation_id: string
}

export interface Conversation {
  id: string
  title: string
  messages: Message[]
  created_at: string
  updated_at: string
}
