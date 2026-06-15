from openai import OpenAI
from app.core.config import settings
from app.db.repositories.leads_repo import get_leads
from app.db.repositories.students_repo import get_students
from app.db.repositories.briefs_repo import create_brief

_client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_daily_brief() -> dict:
    leads = get_leads()
    students = get_students()

    new_leads = [l for l in leads if l.get("status") == "new"]
    active_students = [s for s in students if s.get("status") == "active"]

    prompt = f"""AdimOS günlük yönetim özeti:

- Müşteri adayı: {len(leads)} toplam, {len(new_leads)} yeni
- Öğrenci: {len(students)} toplam, {len(active_students)} aktif

Kısa, madde madde, Türkçe özet yaz. 5 maddeyi geçme."""

    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    return create_brief("Günlük Özet", response.choices[0].message.content, "daily_brief")
