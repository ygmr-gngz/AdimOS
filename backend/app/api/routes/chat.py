from fastapi import APIRouter
from app.schemas.chat import ChatRequest, ChatResponse
from app.modules.knowledge.rag import query
from app.db.repositories.agents_repo import create_conversation, get_messages, create_message

router = APIRouter()


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    conversation_id = request.conversation_id

    if not conversation_id:
        conv = create_conversation("default", "knowledge")
        conversation_id = conv["id"]

    history = get_messages(conversation_id)
    openai_history = [{"role": m["role"], "content": m["content"]} for m in history]

    result = query(request.message, openai_history)

    create_message(conversation_id, "user", request.message)
    create_message(conversation_id, "assistant", result["answer"])

    return ChatResponse(
        answer=result["answer"],
        citations=result["citations"],
        conversation_id=conversation_id,
    )
