from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: DocumentStatus
    created_at: datetime

class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    status: DocumentStatus
    created_at: datetime
   
