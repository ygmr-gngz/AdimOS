from openai import OpenAI
from app.core.config import settings

_client = OpenAI(api_key=settings.OPENAI_API_KEY)

_SYSTEM = """Kullanıcının mesajını analiz et ve hangi ajana yönlendirilmesi gerektiğini belirle.
Yalnızca şu değerlerden birini döndür: knowledge, crm, ceo, learning, automation

knowledge: bilgi tabanı soruları, mevzuat, muhasebe
crm: müşteri, lead, satış
ceo: genel işletme durumu, strateji
learning: öğrenci, eğitim, kurs
automation: otomasyon, görev, zamanlama"""

_VALID = {"knowledge", "crm", "ceo", "learning", "automation"}


def route_intent(transcript: str) -> str:
    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": transcript},
        ],
        max_tokens=10,
    )
    intent = response.choices[0].message.content.strip().lower()
    return intent if intent in _VALID else "knowledge"
