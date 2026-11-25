from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.content import (
    LectureCompletionOut,
    LectureCreateRequest,
    LectureOut,
    LectureReorderRequest,
    LectureUpdateRequest,
)
from app.services import content_service
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/api/lectures", tags=["Lectures"])


@router.get("", response_model=PaginatedResponse[LectureOut])
def list_lectures(
    course_id: int = Query(...),
    module_id: Optional[int] = Query(None),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List lectures for an authorized course."""
    return content_service.list_lectures(
        db=db,
        course_id=course_id,
        module_id=module_id,
        current_user=current_user,
        page=pagination.page,
        page_size=pagination.page_size,
        sort_by=pagination.sort_by,
        sort_order=pagination.sort_order,
    )


@router.post("", response_model=LectureOut, status_code=status.HTTP_201_CREATED)
def create_lecture(
    payload: LectureCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Create a lecture in an assigned course (Admin or assigned Instructor)."""
    return content_service.create_lecture(db, payload, current_user)


@router.put("/reorder", response_model=List[LectureOut])
def reorder_lectures(
    payload: LectureReorderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Reorder lectures within a course module."""
    return content_service.reorder_lectures(db, payload, current_user)


@router.get("/{lecture_id}", response_model=LectureOut)
def get_lecture(
    lecture_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """View lecture metadata and completion status."""
    return content_service.get_lecture(db, lecture_id, current_user)


@router.put("/{lecture_id}", response_model=LectureOut)
def update_lecture(
    lecture_id: int,
    payload: LectureUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Update lecture metadata."""
    return content_service.update_lecture(db, lecture_id, payload, current_user)


@router.delete("/{lecture_id}", response_model=MessageResponse)
def delete_lecture(
    lecture_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Delete a lecture and any associated uploaded video."""
    content_service.delete_lecture(db, lecture_id, current_user)
    return MessageResponse(message="Lecture deleted successfully.")


@router.post("/{lecture_id}/upload-video", response_model=LectureOut)
async def upload_lecture_video(
    lecture_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Upload a lecture video file (.mp4, .webm, .mov)."""
    return await content_service.upload_lecture_video(db, lecture_id, file, current_user)


@router.get("/{lecture_id}/video")
def download_lecture_video(
    lecture_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download/stream an authorized lecture's uploaded video file."""
    return content_service.download_lecture_video(db, lecture_id, current_user)


@router.post("/{lecture_id}/complete", response_model=LectureCompletionOut)
def complete_lecture(
    lecture_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("student")),
):
    """Mark a lecture as completed for the authenticated enrolled student."""
    return content_service.mark_lecture_completed(db, lecture_id, current_user)
