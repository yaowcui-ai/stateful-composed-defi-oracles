from __future__ import annotations

import csv
import hashlib
from pathlib import Path


HERE = Path(__file__).resolve().parent
PHASE = HERE.parent
PROJECT = PHASE.parent
OUTPUT = HERE / "SOURCE_ARTIFACT_SHA256.csv"

EXCLUDED_PARTS = {"node_modules", "cache", "__pycache__", HERE.name}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def selected_files() -> list[Path]:
    files = [
        path for path in PHASE.rglob("*")
        if path.is_file() and not EXCLUDED_PARTS.intersection(path.parts)
    ]
    for pattern in ("JOURNAL_MANUSCRIPT_V0.4*", "JOURNAL_MANUSCRIPT_V0.5*"):
        files.extend(path for path in (PROJECT / "journal_manuscript_phase").glob(pattern) if path.is_file())
    return sorted(set(files), key=lambda p: str(p).lower())


def main() -> None:
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "sha256"])
        writer.writeheader()
        for path in selected_files():
            writer.writerow({
                "path": str(path.resolve()),
                "bytes": path.stat().st_size,
                "sha256": digest(path),
            })


if __name__ == "__main__":
    main()
