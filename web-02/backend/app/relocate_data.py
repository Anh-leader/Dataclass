"""Repair file references when an existing local database moves with the project."""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

from .config import DATA_DIR, UPLOAD_DIR, ARTIFACT_DIR
from .database import SessionLocal, engine
from .models import Assignment, Artifact


def relocate_path(value: str, directory: Path) -> str:
    if Path(value).is_file():
        return value
    normalized = value.replace("\\", "/")
    marker = f"/var/{directory.name}/"
    if marker not in normalized:
        return value
    relative = normalized.rsplit(marker, 1)[1]
    candidate = (directory / relative).resolve()
    if candidate.is_relative_to(directory.resolve()) and candidate.is_file():
        return str(candidate)
    return value


def main():
    if engine.dialect.name != "sqlite" or engine.url.database == ":memory:":
        return
    with SessionLocal() as db:
        changes = 0
        for assignment in db.scalars(select(Assignment)):
            items = json.loads(assignment.dataset_json or "[]")
            changed = False
            for item in items:
                original = item.get("path", "")
                relocated = relocate_path(original, UPLOAD_DIR)
                if relocated != original:
                    item["path"] = relocated
                    changed = True
                    changes += 1
            if changed:
                assignment.dataset_json = json.dumps(items, ensure_ascii=False)
        for artifact in db.scalars(select(Artifact)):
            relocated = relocate_path(artifact.local_path, ARTIFACT_DIR)
            if relocated != artifact.local_path:
                artifact.local_path = relocated
                changes += 1
        if not changes:
            print("Local file references are ready.")
            return
        backup_dir = DATA_DIR / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = backup_dir / f"before-relocation-{stamp}-{uuid4().hex[:6]}.sqlite3"
        with sqlite3.connect(engine.url.database) as source, sqlite3.connect(backup) as target:
            source.backup(target)
        db.commit()
        print(f"Repaired {changes} file references. Database backup: {backup}")


if __name__ == "__main__":
    main()
