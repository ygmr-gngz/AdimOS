import time
import logging
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.chat import ChatRequest, ChatResponse
from app.modules.knowledge.rag import query
from app.db.repositories import chat_repo
from app.db.repositories.audit_repo import log_action
from app.core.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

RATE_LIMIT = 20  # requests per minute per user
_rate_store: dict[str, list[float]] = {}


def _check_rate(user_id: str):
    now = time.time()
    times = [t for t in _rate_store.get(user_id, []) if now - t < 60]
    if len(times) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Çok fazla istek. Bir dakika bekleyin.")
    times.append(now)
    _rate_store[user_id] = times


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, user=Depends(get_current_user)):
    _check_rate(user.id)

    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Mesaj boş olamaz")
    if len(message) > 4000:
        raise HTTPException(status_code=400, detail="Mesaj 4000 karakterden uzun olamaz")

    # Get or create conversation
    conversation_id = request.conversation_id
    if not conversation_id:
        title = " ".join(message.split()[:7])
        conv = chat_repo.create_conversation(user.id, title)
        conversation_id = conv["id"] if conv else None

    # Load history
    history: list[dict] = []
    if conversation_id:
        msgs = chat_repo.get_messages(conversation_id)
        history = [{"role": m["role"], "content": m["content"]} for m in msgs if m["role"] in ("user", "assistant")]

    # RAG query
    try:
        result = query(message, history, user_id=user.id)
    except Exception as e:
        logger.error(f"[chat] RAG hatası: {e}")
        return ChatResponse(
            success=False,
            answer="Şu an yanıt üretemiyorum. Lütfen daha sonra tekrar deneyin.",
            sources=[],
            used_rag=False,
            conversation_id=conversation_id,
        )

    # Save to DB
    if conversation_id:
        chat_repo.create_message(conversation_id, user.id, "user", message)
        chat_repo.create_message(
            conversation_id, user.id, "assistant", result["answer"],
            sources=result.get("sources", []),
            used_rag=result.get("used_rag", False),
        )
        chat_repo.touch_conversation(conversation_id)

    log_action(
        user_id=user.id,
        user_email=user.email,
        action="chat.message",
        details={"used_rag": result.get("used_rag"), "chunk_count": len(result.get("sources", []))},
    )

    return ChatResponse(
        success=result.get("success", True),
        answer=result["answer"],
        sources=result.get("sources", []),
        used_rag=result.get("used_rag", False),
        conversation_id=conversation_id,
    )


@router.get("/conversations")
def list_conversations(user=Depends(get_current_user)):
    return {"conversations": chat_repo.get_conversations(user.id)}


@router.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(conversation_id: str, user=Depends(get_current_user)):
    msgs = chat_repo.get_messages(conversation_id)
    logger.info(f"[chat] {len(msgs)} mesaj döndü — user={user.id}")
    return {"messages": msgs}


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, user=Depends(get_current_user)):
    chat_repo.delete_conversation(conversation_id)
    log_action(user_id=user.id, user_email=user.email, action="chat.delete_conversation", resource=conversation_id)
    return {"ok": True}
