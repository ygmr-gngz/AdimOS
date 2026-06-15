from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class StudentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    GRADUATED = "graduated"
    FAILED = "failed"

class StudentCreate(BaseModel):
    name: str
    surname: str
    email: str
    phone:str
    status: StudentStatus

class StudentResponse(BaseModel):
    id: str
    name: str
    surname: str
    email: str
    phone:str
    status: StudentStatus
    created_at: datetime
    updated_at: datetime

class ExamAttempt(BaseModel):
    student_id: str
    exam_name: str
    score: float
    attempt_date: datetime