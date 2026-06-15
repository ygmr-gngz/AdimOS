from pydantic import BaseModel


class ChatRequest(BaseModel):
    message:str
    conversation_id:str | None = None

class Citation(BaseModel):
    document_name:str
    page: int | None = None
    passage: str

class ChatResponse(BaseModel):
    answer:str
    citations: list[Citation]
    conversation_id:str