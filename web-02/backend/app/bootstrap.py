"""Create the first teacher account for an empty database."""
import os
from getpass import getpass

from alembic import command
from alembic.config import Config

from .config import BASE_DIR
from .database import SessionLocal
from .models import User
from .security import hash_password


def main():
    migration = Config(str(BASE_DIR / "backend" / "alembic.ini"))
    command.upgrade(migration, "head")
    email = (os.getenv("BOOTSTRAP_TEACHER_EMAIL") or input("Teacher email: ")).strip().lower()
    full_name = (os.getenv("BOOTSTRAP_TEACHER_NAME") or input("Teacher name: ")).strip()
    password = os.getenv("BOOTSTRAP_TEACHER_PASSWORD") or getpass("Teacher password (12+ chars): ")
    if len(password) < 12 or len(password) > 128:
        raise SystemExit("Password must contain between 12 and 128 characters.")
    db = SessionLocal()
    try:
        if db.query(User).filter_by(role="teacher").first():
            raise SystemExit("A teacher already exists; bootstrap only works on an empty teacher account set.")
        if db.query(User).filter_by(email=email).first():
            raise SystemExit("This email is already registered.")
        db.add(User(email=email, full_name=full_name, password_hash=hash_password(password), role="teacher"))
        db.commit()
        print(f"Teacher account created: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
