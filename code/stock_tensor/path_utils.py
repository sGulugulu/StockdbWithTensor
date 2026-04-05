from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def repo_relative_path(path: str | Path) -> str:
    candidate = Path(path)
    if not candidate.is_absolute():
        return candidate.as_posix()
    try:
        return candidate.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return candidate.as_posix()


def path_relative_to(base_dir: str | Path, target: str | Path) -> str:
    base = Path(base_dir).resolve()
    destination = Path(target).resolve()
    try:
        return Path(os.path.relpath(destination, start=base)).as_posix()
    except ValueError:
        return destination.as_posix()
