"""Dashboard router – role-based overview endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.authorization import get_user_role
from app.services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("", summary="Get role-based dashboard")
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    role = get_user_role(current_user)
    if role == "admin":
        return dashboard_service.admin_dashboard(db)
    elif role == "instructor":
        return dashboard_service.instructor_dashboard(db, current_user)
    else:
        return dashboard_service.student_dashboard(db, current_user)
