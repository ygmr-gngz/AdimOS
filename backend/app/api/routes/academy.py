from fastapi import APIRouter, HTTPException
from app.schemas.academy import StudentCreate, ExamAttempt
from app.modules.academy.service import (
    create_student, get_all_students, get_student, update_student, delete_student,
    add_exam_attempt, get_student_attempts, get_student_average, get_learning_plan,
)

router = APIRouter()


@router.post("/students")
def add_student(data: StudentCreate):
    return create_student(data)


@router.get("/students")
def list_students():
    return get_all_students()


@router.get("/students/{student_id}")
def get_student_by_id(student_id: str):
    student = get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Öğrenci bulunamadı")
    return student


@router.delete("/students/{student_id}")
def remove_student(student_id: str):
    delete_student(student_id)
    return {"message": "Öğrenci silindi"}


@router.post("/students/{student_id}/attempts")
def add_attempt(student_id: str, data: ExamAttempt):
    return add_exam_attempt(student_id, data.exam_name, data.score)


@router.get("/students/{student_id}/attempts")
def get_attempts(student_id: str):
    return get_student_attempts(student_id)


@router.get("/students/{student_id}/average")
def get_average(student_id: str):
    return {"student_id": student_id, "average_score": get_student_average(student_id)}


@router.post("/students/{student_id}/learning-plan")
def learning_plan(student_id: str, topic: str):
    return {"student_id": student_id, "topic": topic, "plan": get_learning_plan(student_id, topic)}
