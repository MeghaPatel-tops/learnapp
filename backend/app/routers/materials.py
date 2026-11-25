from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.content import StudyMaterialOut
from app.services import content_service
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/api/materials", tags=["Study Materials"])


@router.get("", response_model=PaginatedResponse[StudyMaterialOut])
def list_materials(
    course_id: int = Query(...),
    module_id: Optional[int] = Query(None),
    lecture_id: Optional[int] = Query(None),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List study materials for an authorized course."""
    return content_service.list_materials(
        db=db,
        course_id=course_id,
        module_id=module_id,
        lecture_id=lecture_id,
        current_user=current_user,
        page=pagination.page,
        page_size=pagination.page_size,
        sort_by=pagination.sort_by,
        sort_order=pagination.sort_order,
    )


@router.post("", response_model=StudyMaterialOut, status_code=status.HTTP_201_CREATED)
async def upload_material(
    course_id: int = Form(...),
    title: str = Form(..., min_length=2, max_length=200),
    description: Optional[str] = Form(None),
    module_id: Optional[int] = Form(None),
    lecture_id: Optional[int] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Upload a PDF/PPT/document study material for an assigned course."""
    return await content_service.upload_study_material(
        db=db,
        course_id=course_id,
        title=title,
        description=description,
        module_id=module_id,
        lecture_id=lecture_id,
        file=file,
        current_user=current_user,
    )


@router.get("/{material_id}/download")
def download_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download an authorized study material file."""
    return content_service.download_study_material(db, material_id, current_user)


@router.delete("/{material_id}", response_model=MessageResponse)
def delete_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Delete a study material (Admin or assigned Instructor)."""
    content_service.delete_study_material(db, material_id, current_user)
    return MessageResponse(message="Study material deleted successfully.")
