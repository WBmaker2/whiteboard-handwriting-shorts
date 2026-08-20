#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import venv
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
VENV_ROOT = SKILL_ROOT / ".venv"
DEPENDENCIES = {
    "cv2": "opencv-python",
    "numpy": "numpy",
    "av": "av",
    "PIL": "Pillow",
    "google.genai": "google-genai",
}


def interpreter() -> Path:
    if sys.platform.startswith("win"):
        return VENV_ROOT / "Scripts" / "python.exe"
    return VENV_ROOT / "bin" / "python"


def can_import(python: Path, name: str) -> bool:
    return subprocess.run(
        [str(python), "-c", f"import {name}"],
        capture_output=True,
    ).returncode == 0


def main() -> int:
    check_only = "--check" in sys.argv
    python = interpreter()
    if not python.exists():
        if check_only:
            print(f"[error] 가상환경이 없습니다: {VENV_ROOT}", file=sys.stderr)
            return 1
        venv.create(str(VENV_ROOT), with_pip=True)

    missing = [
        package
        for import_name, package in DEPENDENCIES.items()
        if not can_import(python, import_name)
    ]
    if missing and check_only:
        print(f"[error] 누락된 패키지: {', '.join(missing)}", file=sys.stderr)
        return 1
    if missing:
        result = subprocess.run(
            [str(python), "-m", "pip", "install", "--quiet", *missing],
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            return result.returncode

    print(f"ENV_PY={python}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
