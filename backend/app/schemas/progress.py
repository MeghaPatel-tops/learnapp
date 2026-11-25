from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class AssignmentProgressItem(BaseModel):
    assignment_id: int
    title: str
    max_marks: float
    passing_marks: float
    latest_status: str
    marks_obtained: Optional[float] = None
    passed: bool


class QuizProgressItem(BaseModel):
    quiz_id: int
    title: str
    total_marks: float
    passing_marks: float
    attempts_used: int
    best_score: Optional[float] = None
    passed: bool


class CourseProgressOut(BaseModel):
    student_id: int
    course_id: int
    course_name: str
    enrollment_status: str
    completed_lectures: int
    total_lectures: int
    pending_lectures: int
    lecture_completion_pct: float
    assignments_passed: int
    total_assignments: int
    assignment_items: List[AssignmentProgressItem]
    quizzes_passed: int
    total_quizzes: int
    quiz_items: List[QuizProgressItem]
    attendance_percentage: float
    overall_progress_pct: float
    is_course_completed: bool
    completed_at: Optional[datetime] = None
