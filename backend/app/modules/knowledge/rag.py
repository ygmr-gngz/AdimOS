from openai import OpenAI
from app.core.config import settings
from app.modules.knowledge.retriever import retrieve

_client = OpenAI(api_key=settings.OPENAI_API_KEY)

_SYSTEM = """Sen AdimOS'un muhasebe ve danışmanlık asistanısın. Sağlanan bağlam parçalarını kullanarak kullanıcıya Türkçe yardım et.
Bağlam sınav soruları veya belge parçaları içeriyorsa bile bu bilgileri kullanarak kapsamlı bir cevap üret.
Bağlamda hiç ilgili bilgi yoksa ve kendi bilginle de cevaplayamıyorsan "Bu konuda yeterli bilgim bulunmuyor." de.
Muhasebe, vergi, SGK, mali tablolar gibi mesleki konularda genel bilginle de destekleyerek cevap ver."""


def query(user_message: str, conversation_history: list[dict] | None = None) -> dict:
    chunks = retrieve(user_message, match_count=10)
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
