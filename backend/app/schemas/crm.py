from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    LOST = "lost"
   

class LeadCreate(BaseModel):
    name: str
    email: str
    phone: str | None = None
    status: LeadStatus
    

class LeadResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str | None = None
    status: LeadStatus
    created_at: datetime

class LeadUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    status: LeadStatus | None = None