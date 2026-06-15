from app.db.repositories.students_repo import (
    create_student, get_students, get_student, update_student, delete_student,
)
from app.schemas.academy import StudentCreate


def add_student(data: StudentCreate) -> dict:
    return create_student(data.name, data.surname, data.email, data.phone, data.status.value)


def list_students() -> list[dict]:
    return get_students()


def fetch_student(student_id: str) -> dict | None:
    return get_student(student_id)


def modify_student(student_id: str, updates: dict) -> dict | None:
    return update_student(student_id, updates)


def remove_student(student_id: str) -> list[dict]:
    return delete_student(student_id)
