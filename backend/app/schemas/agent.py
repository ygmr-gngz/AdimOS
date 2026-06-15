from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class AgentType(str, Enum):
    KNOWLEDGE = "knowledge"
    VOICE = "voice"
    CEO = "ceo"
    CRM = "crm"
    FOLLOWUP = "followup"
    LEARNING = "learning"
    AUTOMATION = "automation"

class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentRun(BaseModel):
    agent_type: AgentType
    status: AgentStatus
    started_at: datetime
    finished_at: datetime | None = None
    result_summary: str | None = None

class AgentResponse(BaseModel):
    agents: list[AgentRun]

