from app.modules.agents.base import BaseAgent
from app.db.repositories.students_repo import get_student, get_exam_attempts


class LearningAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "Sen SGS Academy'nin öğrenme asistanısın. Öğrencilerin gelişimini takip eder, kişiselleştirilmiş öneriler sunarsın. Türkçe yanıt ver."
        )

    def analyze_student(self, student_id: str) -> str:
        student = get_student(student_id)
        if not student:
            return "Öğrenci bulunamadı."
        attempts = get_exam_attempts(student_id)
        return self.chat(
            f"Öğrencinin profilini analiz et ve öneriler sun:\nÖğrenci: {student}\nSınav geçmişi: {attempts}"
        )

    def create_study_plan(self, student_id: str, topic: str) -> str:
        student = get_student(student_id)
        if not student:
            return "Öğrenci bulunamadı."
        return self.chat(
            f"{student['name']} {student['surname']} için '{topic}' konusunda haftalık çalışma planı oluştur."
        )
