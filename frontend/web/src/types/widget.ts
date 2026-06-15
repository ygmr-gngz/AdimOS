export type WidgetMsgRole = 'visitor' | 'assistant'
export type WidgetFileKind = 'pdf' | 'excel' | 'csv' | 'other'

export interface WidgetFile {
  id: string
  name: string
  kind: WidgetFileKind
  size: number
}

export interface WidgetMessage {
  id: string
  role: WidgetMsgRole
  content: string
  created_at: string
  input_type?: 'text' | 'voice' | 'file'
  files?: WidgetFile[]
}

export interface WidgetConversation {
  id: string
  site_id: string
  visitor_id: string
  visitor_name?: string
  started_at: string
  last_message_at: string
  message_count: number
  file_count: number
  status: 'active' | 'closed'
  messages?: WidgetMessage[]
}

export interface WidgetStats {
  total_conversations: number
  today_conversations: number
  active_conversations: number
  total_file_uploads: number
}

export interface WidgetChatResponse {
  answer: string
  conversation_id: string
}

export interface WidgetVoiceResponse {
  transcript: string
  answer: string
  answer_audio_base64: string
  conversation_id: string
}
