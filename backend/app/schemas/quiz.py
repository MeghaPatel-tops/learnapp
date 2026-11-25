from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class QuizOptionCreate(BaseModel):
    option_text: str = Field(..., min_length=1, max_length=500)
    is_correct: bool = False
    sequence_order: int = Field(1, ge=1)


class QuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=2, max_length=5000)
    marks: Decimal = Field(Decimal("1.00"), gt=Decimal("0.00"), le=Decimal("100.00"))
    sequence_order: int = Field(1, ge=1)
    options: List[QuizOptionCreate] = Field(..., min_length=2, max_length=10)

    @model_validator(mode="after")
    def validate_one_correct_option(self):
        correct_count = sum(1 for o in self.options if o.is_correct)
        if correct_count != 1:
            raise ValueError("Each MCQ question must have exactly one option marked is_correct=true.")
        return self


class QuizCreateRequest(BaseModel):
    course_id: int
    batch_id: Optional[int] = None
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    total_marks: Decimal = Field(..., gt=Decimal("0.00"), le=Decimal("1000.00"))
    passing_marks: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("1000.00"))
    duration_minutes: int = Field(..., ge=1, le=600)
    available_from: datetime
    available_until: datetime
    allow_retakes: bool = False
    max_attempts: int = Field(1, ge=1, le=20)
    show_correct_answers: bool = True
    is_published: bool = True
    questions: List[QuestionCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_quiz_rules(self):
        if self.available_until <= self.available_from:
            raise ValueError("available_until must be after available_from.")
        if self.passing_marks > self.total_marks:
            raise ValueError("passing_marks cannot exceed total_marks.")
        if not self.allow_retakes and self.max_attempts != 1:
            self.max_attempts = 1
        return self


class QuizUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    total_marks: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    passing_marks: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    duration_minutes: Optional[int] = Field(None, ge=1, le=600)
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    allow_retakes: Optional[bool] = None
    max_attempts: Optional[int] = Field(None, ge=1, le=20)
    show_correct_answers: Optional[bool] = None
    is_published: Optional[bool] = None


class QuizOptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    option_text: str
    sequence_order: int
    is_correct: Optional[bool] = None


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quiz_id: int
    question_text: str
    marks: Decimal
    sequence_order: int
    options: List[QuizOptionOut] = []


class QuizOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    batch_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    total_marks: Decimal
    passing_marks: Decimal
    duration_minutes: int
    available_from: datetime
    available_until: datetime
    allow_retakes: bool
    max_attempts: int
    show_correct_answers: bool
    is_published: bool
    question_count: int = 0
    created_at: datetime


class QuizDetailOut(QuizOut):
    questions: List[QuestionOut] = []


class SaveAnswerRequest(BaseModel):
    question_id: int
    selected_option_id: int


class QuizAnswerReviewOut(BaseModel):
    question_id: int
    selected_option_id: Optional[int] = None
    is_correct: Optional[bool] = None
    marks_awarded: Decimal
    correct_option_id: Optional[int] = None


class QuizAttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quiz_id: int
    student_id: int
    attempt_number: int
    started_at: datetime
    expires_at: datetime
    submitted_at: Optional[datetime] = None
    status: str
    score: Decimal
    is_passed: bool
    questions: List[QuestionOut] = []
    answers: List[QuizAnswerReviewOut] = []
