from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, utcnow


class Course(Base, TimestampMixin):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    duration_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        SqlEnum("draft", "published", "archived", name="course_status_enum"),
        default="draft",
        nullable=False,
        index=True,
    )
    primary_instructor_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("instructors.id", ondelete="SET NULL"), nullable=True
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    modules: Mapped[List["CourseModule"]] = relationship(
        "CourseModule", back_populates="course", cascade="all, delete-orphan", order_by="CourseModule.sequence_order"
    )
    course_instructors: Mapped[List["CourseInstructor"]] = relationship(
        "CourseInstructor", back_populates="course", cascade="all, delete-orphan"
    )
    batches: Mapped[List["Batch"]] = relationship("Batch", back_populates="course")
    enrollments: Mapped[List["Enrollment"]] = relationship("Enrollment", back_populates="course")


class CourseInstructor(Base):
    __tablename__ = "course_instructors"
    __table_args__ = (UniqueConstraint("course_id", "instructor_id", name="uq_course_instructor"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    instructor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("instructors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    course: Mapped["Course"] = relationship("Course", back_populates="course_instructors")


class CourseModule(Base, TimestampMixin):
    __tablename__ = "course_modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sequence_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    course: Mapped["Course"] = relationship("Course", back_populates="modules")


class Batch(Base, TimestampMixin):
    __tablename__ = "batches"
    __table_args__ = (CheckConstraint("capacity > 0", name="ck_batch_capacity_positive"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    instructor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("instructors.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    class_days: Mapped[str] = mapped_column(String(100), nullable=False)
    class_timing: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        SqlEnum("upcoming", "active", "closed", "archived", name="batch_status_enum"),
        default="upcoming",
        nullable=False,
        index=True,
    )

    course: Mapped["Course"] = relationship("Course", back_populates="batches")
    batch_students: Mapped[List["BatchStudent"]] = relationship(
        "BatchStudent", back_populates="batch", cascade="all, delete-orphan"
    )


class Enrollment(Base, TimestampMixin):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_enrollment_student_course"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        SqlEnum("active", "completed", "dropped", name="enrollment_status_enum"),
        default="active",
        nullable=False,
        index=True,
    )
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    course: Mapped["Course"] = relationship("Course", back_populates="enrollments")


class BatchStudent(Base, TimestampMixin):
    __tablename__ = "batch_students"
    __table_args__ = (UniqueConstraint("batch_id", "student_id", name="uq_batch_student"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    enrollment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("enrollments.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        SqlEnum("active", "removed", "completed", name="batch_student_status_enum"),
        default="active",
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    batch: Mapped["Batch"] = relationship("Batch", back_populates="batch_students")
