from openai import OpenAI
from app.core.config import settings
from app.modules.knowledge.retriever import retrieve

_client = OpenAI(api_key=settings.OPENAI_API_KEY)

_SYSTEM = """Sen AdimOS'un bilgi asistanısın. Yalnızca sağlanan bağlam içindeki bilgileri kullanarak Türkçe cevap ver.
Bağlamda cevap yoksa "Bu konuda bilgim bulunmuyor." de. Cevabını kısa ve net tut."""


def query(user_message: str, conversation_history: list[dict] | None = None) -> dict:
    chunks = retrieve(user_message)
    context = "\n\n".join([c["chunk_data"] for c in chunks])

    messages = [{"role": "system", "content": _SYSTEM + f"\n\nBağlam:\n{context}"}]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )

    answer = response.choices[0].message.content
    citations = [
        {"document_name": c.get("document_id", ""), "passage": c["chunk_data"][:200]}
        for c in chunks
    ]

    return {"answer": answer, "citations": citations}
