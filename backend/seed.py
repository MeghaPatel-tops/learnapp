"""Seed script – insert roles and default admin account."""

import sys

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.models.user import Role, User
from app.utils.security import hash_password


def seed():
    db = SessionLocal()
    try:
        # 1. Roles
        role_defs = [
            ("admin", "System administrator with full access"),
            ("instructor", "Teaching staff managing courses and batches"),
            ("student", "Learner enrolled in courses"),
        ]
        created_roles = {}
        for name, desc in role_defs:
            existing = db.execute(select(Role).where(Role.name == name)).scalar_one_or_none()
            if existing is None:
                role = Role(name=name, description=desc)
                db.add(role)
                db.flush()
                created_roles[name] = role
                print(f"  [+] Role created: {name}")
            else:
                created_roles[name] = existing
                print(f"  [=] Role exists:  {name}")

        # 2. Default admin
        admin_email = "admin@lms-institute.com"
        admin_exists = db.execute(select(User).where(User.email == admin_email)).scalar_one_or_none()
        if admin_exists is None:
            admin_user = User(
                role_id=created_roles["admin"].id,
                full_name="System Administrator",
                email=admin_email,
                password_hash=hash_password("Admin@123456"),
                is_active=True,
            )
            db.add(admin_user)
            print(f"  [+] Admin created: {admin_email} / Admin@123456")
        else:
            print(f"  [=] Admin exists:  {admin_email}")

        db.commit()
        print("\nSeed completed successfully.")
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
