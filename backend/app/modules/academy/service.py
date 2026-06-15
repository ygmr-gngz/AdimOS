from app.modules.academy.students import add_student, list_students, fetch_student, modify_student, remove_student
from app.modules.academy.attempts import record_attempt, list_attempts, calculate_average
from app.modules.academy.learning_plan import generate_learning_plan
from app.schemas.academy import StudentCreate


def create_student(data: StudentCreate) -> dict:
    return add_student(data)


def get_all_students() -> list[dict]:
    return list_students()


def get_student(student_id: str) -> dict | None:
    return fetch_student(student_id)


def update_student(student_id: str, updates: dict) -> dict | None:
    return modify_student(student_id, updates)


def delete_student(student_id: str) -> list[dict]:
    return remove_student(student_id)


def add_exam_attempt(student_id: str, exam_name: str, score: float) -> dict:
    return record_attempt(student_id, exam_name, score)


def get_student_attempts(student_id: str) -> list[dict]:
    return list_attempts(student_id)


def get_student_average(student_id: str) -> float:
    return calculate_average(student_id)


def get_learning_plan(student_id: str, topic: str) -> str:
    return generate_learning_plan(student_id, topic)
