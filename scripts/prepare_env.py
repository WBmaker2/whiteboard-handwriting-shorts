#!/usr/bin/env python3
"""스킬 전용 Python 가상환경의 패키지를 계획·확인·적용한다."""

from __future__ import annotations

import argparse
import subprocess
import sys
import venv
from pathlib import Path

from environment_checks import ensure_supported_python

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
    try:
        result = subprocess.run(
            [str(python), "-c", f"import {name}"],
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def missing_packages(python: Path) -> list[str]:
    if not python.is_file():
        return list(DEPENDENCIES.values())
    return [
        package
        for import_name, package in DEPENDENCIES.items()
        if not can_import(python, import_name)
    ]


def current_python_command() -> str:
    executable = sys.executable
    return f'"{executable}"' if any(character.isspace() for character in executable) else executable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="승인 기반 화이트보드 숏츠 Python 환경 준비")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true", help="가상환경과 패키지를 읽기 전용으로 확인")
    action.add_argument("--plan", action="store_true", help="생성·설치 계획만 출력")
    action.add_argument("--apply", action="store_true", help="사용자 승인 후 가상환경과 패키지 적용")
    parser.add_argument("--approved", action="store_true", help="현재 대화에서 적용을 승인했음을 확인")
    return parser.parse_args()


def print_plan(python: Path, missing: list[str]) -> None:
    print("스킬 전용 Python 가상환경 패키지 준비 계획입니다.")
    print(f"VENV_ROOT={VENV_ROOT}")
    print(f"ENV_PY={python}")
    if python.exists():
        print("VENV_ACTION=keep-existing")
    else:
        print("VENV_ACTION=create-with-venv")
    if missing:
        print(f"PIP_INSTALL={' '.join(missing)}")
    else:
        print("PIP_INSTALL=none")
    print("SYSTEM_TOOLS=manual (Python·Git·FFmpeg·FFprobe는 자동 설치하지 않음)")
    print("적용하려면 사용자 승인 후 --apply --approved를 실행합니다.")


def print_check(python: Path, missing: list[str]) -> int:
    print(f"ENV_PY={python}")
    if not python.exists():
        print("ENV_READY=false")
        print(f"누락: 스킬 전용 가상환경 {VENV_ROOT}")
        return 2
    if missing:
        print("ENV_READY=false")
        print(f"누락된 패키지: {', '.join(missing)}")
        return 2
    print("ENV_READY=true")
    return 0


def apply(python: Path, missing: list[str]) -> int:
    if not python.exists():
        print(f"가상환경 생성: {VENV_ROOT}")
        venv.create(str(VENV_ROOT), with_pip=True)
    if missing:
        print(f"패키지 설치: {', '.join(missing)}")
        result = subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                *missing,
            ],
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print("패키지 설치에 실패했습니다.", file=sys.stderr)
            print("네트워크·권한·디스크 공간을 확인한 뒤 아래 순서로 재시도하세요.", file=sys.stderr)
            launcher = current_python_command()
            print(f"{launcher} {Path(__file__).resolve()} --check", file=sys.stderr)
            print(f"{launcher} {Path(__file__).resolve()} --plan", file=sys.stderr)
            print(f"{launcher} {Path(__file__).resolve()} --apply --approved", file=sys.stderr)
            return result.returncode or 1
    return print_check(python, missing_packages(python))


def main() -> int:
    try:
        ensure_supported_python()
    except RuntimeError as error:
        print(f"[error] {error}", file=sys.stderr)
        print("먼저 references/environment-setup.md의 Python 설치 방법을 확인하세요.", file=sys.stderr)
        return 2

    args = parse_args()
    python = interpreter()
    missing = missing_packages(python)
    if args.check:
        return print_check(python, missing)
    if args.plan:
        print_plan(python, missing)
        return 0
    if not args.approved:
        print("사용자의 명시적 승인 후 --approved를 포함해 다시 실행해야 합니다.", file=sys.stderr)
        print("먼저 --plan 결과를 사용자에게 보여주세요.", file=sys.stderr)
        return 3
    try:
        return apply(python, missing)
    except (OSError, subprocess.SubprocessError, RuntimeError) as error:
        print(f"[error] 환경 준비에 실패했습니다: {error}", file=sys.stderr)
        print("기존 .venv를 삭제하지 말고, 원인을 해결한 뒤 --check → --plan → --apply --approved 순서로 재시도하세요.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
