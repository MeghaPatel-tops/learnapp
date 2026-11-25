"""Shared test fixtures – DB session, TestClient, user helpers."""

import pytest
import sqlalchemy
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.database import Base, get_db
from app.main import app
from app.models.user import Role, User
from app.utils.security import hash_password

settings = get_settings()

engine = create_engine(settings.TEST_DATABASE_URL, pool_pre_ping=True)
TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Ensure tables exist in lms_test_db and disable rate limiting for tests."""
    Base.metadata.create_all(bind=engine)
    # Disable SlowAPI rate limiter so test logins don't get throttled
    from app.middleware.logging_mw import limiter
    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest.fixture()
def db():
    """Provide a transactional DB session that rolls back after each test.

    Uses the nested-transaction (SAVEPOINT) pattern so that service-level
    ``session.commit()`` calls write to the savepoint rather than the real DB,
    allowing full rollback after each test.
    """
    connection = engine.connect()
    transaction = connection.begin()          # outer real transaction
    session = TestSessionLocal(bind=connection)

    # Start a SAVEPOINT; every session.commit() will release this savepoint
    # and we immediately open a new one so the next commit() works too.
    nested = connection.begin_nested()

    @sqlalchemy.event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        if trans.nested and not trans._parent.nested:
            nested = connection.begin_nested()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db):
    """TestClient with the DB dependency overridden to use the transactional session."""

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# --------------- Helpers ---------------


def _ensure_roles(db):
    """Create the three roles if missing, return dict name -> Role."""
    roles = {}
    for name, desc in [
        ("admin", "Administrator"),
        ("instructor", "Instructor"),
        ("student", "Student"),
    ]:
        role = db.execute(
            text("SELECT id FROM roles WHERE name = :n"), {"n": name}
        ).fetchone()
        if role is None:
            r = Role(name=name, description=desc)
            db.add(r)
            db.flush()
            roles[name] = r
        else:
            roles[name] = db.get(Role, role[0])
    return roles


def create_test_user(db, *, email, password="Test@12345", role_name="admin", full_name="Test User"):
    """Insert a user and return (User, raw_password)."""
    roles = _ensure_roles(db)
    role = roles[role_name]
    user = User(
        role_id=role.id,
        full_name=full_name,
        email=email,
        password_hash=hash_password(password),
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user, password


def auth_header(client, email, password):
    """Log in and return {'Authorization': 'Bearer <token>'} dict."""
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_user(db):
    user, pw = create_test_user(db, email="admin-test@example.com", role_name="admin", full_name="Admin Test")
    db.commit()
    return user, pw


@pytest.fixture()
def admin_headers(client, admin_user):
    user, pw = admin_user
    return auth_header(client, user.email, pw)


@pytest.fixture()
def instructor_user(db):
    from app.models.user import Instructor
    user, pw = create_test_user(db, email="instr-test@example.com", role_name="instructor", full_name="Instructor Test")
    instr = Instructor(user_id=user.id, employee_code="INS-TEST01", expertise="Python", experience_years=5)
    db.add(instr)
    db.flush()
    db.commit()
    return user, pw


@pytest.fixture()
def instructor_headers(client, instructor_user):
    user, pw = instructor_user
    return auth_header(client, user.email, pw)


@pytest.fixture()
def student_user(db):
    from app.models.user import Student
    user, pw = create_test_user(db, email="student-test@example.com", role_name="student", full_name="Student Test")
    stu = Student(user_id=user.id, student_code="STU-TEST01")
    db.add(stu)
    db.flush()
    db.commit()
    return user, pw


@pytest.fixture()
def student_headers(client, student_user):
    user, pw = student_user
    return auth_header(client, user.email, pw)
