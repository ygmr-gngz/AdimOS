from openai import OpenAI
from app.core.config import settings
from app.db.repositories.students_repo import get_student, get_exam_attempts

_client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_learning_plan(student_id: str, topic: str) -> str:
    student = get_student(student_id)
    if not student:
        return "Öğrenci bulunamadı."

    attempts = get_exam_attempts(student_id)
    avg = round(sum(a["score"] for a in attempts) / len(attempts), 1) if attempts else 0.0

    prompt = f"""{student['name']} {student['surname']} için kişiselleştirilmiş çalışma planı:

Konu: {topic}
Ortalama puan: {avg} ({len(attempts)} sınav)

Haftalık, madde madde Türkçe çalışma planı oluştur."""

    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content
