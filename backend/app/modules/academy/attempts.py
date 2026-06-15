from app.db.repositories.students_repo import create_exam_attempt, get_exam_attempts


def record_attempt(student_id: str, exam_name: str, score: float) -> dict:
    return create_exam_attempt(student_id, exam_name, score)


def list_attempts(student_id: str) -> list[dict]:
    return get_exam_attempts(student_id)


def calculate_average(student_id: str) -> float:
    attempts = get_exam_attempts(student_id)
    if not attempts:
        return 0.0
    return round(sum(a["score"] for a in attempts) / len(attempts), 2)
