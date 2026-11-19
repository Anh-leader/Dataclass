"""Configure an isolated database before pytest imports any application modules."""
import os
import tempfile
from pathlib import Path

import pytest


TEST_DIR = Path(tempfile.mkdtemp(prefix="web02-test-")).resolve()
os.environ["WEB02_DATA_DIR"] = str(TEST_DIR / "var")
os.environ["WEB02_DATABASE_URL"] = f"sqlite:///{TEST_DIR / 'test.sqlite3'}"
os.environ["WEB02_SECRET_KEY"] = "test-secret"
os.environ["WEB02_COOKIE_SECURE"] = "false"
os.environ["WEB02_ENV"] = "development"


@pytest.fixture(autouse=True)
def isolated_database():
    from app.database import engine

    assert Path(engine.url.database).resolve().is_relative_to(TEST_DIR), "Tests must never use the application database"
