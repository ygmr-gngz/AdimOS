from app.core.llm_client import chat as llm_chat

_SYSTEM = """Kullanıcının mesajını analiz et ve hangi ajana yönlendirilmesi gerektiğini belirle.
Yalnızca şu değerlerden birini döndür: knowledge, crm, ceo, learning, automation

knowledge: bilgi tabanı soruları, mevzuat, muhasebe
crm: müşteri, lead, satış
ceo: genel işletme durumu, strateji
learning: öğrenci, eğitim, kurs
automation: otomasyon, görev, zamanlama"""

_VALID = {"knowledge", "crm", "ceo", "learning", "automation"}


def route_intent(transcript: str) -> str:
    intent = llm_chat(
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": transcript},
        ],
        model="gpt-4o-mini",
        temperature=0.0,  # deterministik sınıflandırma
        max_tokens=10,
        caller="intent_router",
    ).strip().lower()
    return intent if intent in _VALID else "knowledge"
