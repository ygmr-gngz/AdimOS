from fastapi import APIRouter
from app.db.repositories.agents_repo import get_conversations, get_messages, delete_conversation

router = APIRouter()

_AGENT_DEFINITIONS = [
    {"id": "knowledge_agent", "name": "Knowledge Agent", "description": "Doküman işleme ve RAG tabanlı bilgi arama", "status": "idle", "icon": "brain", "run_count": 0},
    {"id": "voice_agent",     "name": "Voice Agent",     "description": "Sesli girişleri işleyen ve yönlendiren agent", "status": "idle", "icon": "mic", "run_count": 0},
    {"id": "ceo_agent",       "name": "CEO Agent",       "description": "Günlük ve haftalık yönetici özeti üretir", "status": "idle", "icon": "briefcase", "run_count": 0},
    {"id": "crm_agent",       "name": "CRM Agent",       "description": "Lead skorlama ve müşteri takibi yapar", "status": "idle", "icon": "users", "run_count": 0},
    {"id": "followup_agent",  "name": "Follow-up Agent", "description": "Otomatik takip mesajı taslakları üretir", "status": "idle", "icon": "usercheck", "run_count": 0},
    {"id": "learning_agent",  "name": "Learning Agent",  "description": "Öğrenci analizi ve öğrenme planı oluşturur", "status": "idle", "icon": "bookopen", "run_count": 0},
    {"id": "automation_agent","name": "Automation Agent","description": "YouTube/Instagram içerik üretir ve paylaşır", "status": "idle", "icon": "video", "run_count": 0},
]


@router.get("")
def list_agents():
    return _AGENT_DEFINITIONS


@router.get("/runs")
def list_runs(limit: int = 10):
    return {"runs": []}


@router.get("/conversations")
def list_conversations(user_id: str = "default"):
    return get_conversations(user_id)


@router.get("/conversations/{conversation_id}/messages")
def list_messages(conversation_id: str):
    return get_messages(conversation_id)


@router.delete("/conversations/{conversation_id}")
def remove_conversation(conversation_id: str):
    delete_conversation(conversation_id)
    return {"message": "Konuşma silindi"}
