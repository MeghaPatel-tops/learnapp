"""FastAPI application factory for the LMS backend."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.middleware.exceptions import register_exception_handlers
from app.middleware.logging_mw import RequestLoggingMiddleware, limiter

# Import all routers
from app.routers import (
    announcements,
    assignments,
    attendance,
    auth,
    batches,
    certificates,
    courses,
    dashboard,
    enrollments,
    instructors,
    lectures,
    materials,
    notifications,
    payments,
    progress,
    quizzes,
    reports,
    students,
    submissions,
    users,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-18s  %(levelname)-6s  %(message)s",
)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ----- SlowAPI rate limiter -----
    app.state.limiter = limiter

    # ----- CORS -----
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ----- Request logging -----
    app.add_middleware(RequestLoggingMiddleware)

    # ----- Exception handlers -----
    register_exception_handlers(app)

    # ----- Routers -----
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(students.router)
    app.include_router(instructors.router)
    app.include_router(courses.router)
    app.include_router(batches.router)
    app.include_router(enrollments.router)
    app.include_router(lectures.router)
    app.include_router(materials.router)
    app.include_router(assignments.router)
    app.include_router(submissions.router)
    app.include_router(quizzes.router)
    app.include_router(attendance.router)
    app.include_router(progress.router)
    app.include_router(certificates.router)
    app.include_router(notifications.router)
    app.include_router(announcements.router)
    app.include_router(payments.router)
    app.include_router(dashboard.router)
    app.include_router(reports.router)

    # ----- Health check -----
    @app.get("/api/health", tags=["Health"])
    def health_check():
        return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}

    return app


app = create_app()
