from fastapi import APIRouter
from app.db.repositories.agents_repo import get_conversations, get_messages, delete_conversation

router = APIRouter()


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
