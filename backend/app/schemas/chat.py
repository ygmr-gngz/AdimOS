from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatSource(BaseModel):
    document_id: str
    filename: str
    content_preview: str
    similarity: float


class ChatResponse(BaseModel):
    success: bool
    answer: str
    sources: list[ChatSource] = []
    used_rag: bool = False
    conversation_id: str | None = None
