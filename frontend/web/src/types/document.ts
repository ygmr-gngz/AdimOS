export type DocumentStatus = 'uploaded' | 'processing' | 'indexed' | 'failed'

export type DocumentSourceModule = 'knowledge_center' | 'sgs_academy' | 'crm' | 'content_automation'

export interface Document {
  id: string
  user_id: string
  file_name: string
  file_path: string
  file_size: number
  mime_type: string
  status: DocumentStatus
  chunk_count: number
  source_module: DocumentSourceModule
  sgs_analysis_id?: string | null
  created_at: string
  updated_at: string
}

export interface DocumentChunk {
  id: string
  document_id: string
  content: string
  chunk_index: number
  embedding?: number[]
  created_at: string
}

export interface UploadDocumentResponse {
  document: Document
  message: string
}

export interface ListDocumentsResponse {
  documents: Document[]
  total: number
}
