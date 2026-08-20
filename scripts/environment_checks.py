#!/usr/bin/env python3
"""화이트보드 숏츠 실행 환경을 안전하게 확인하는 공통 함수."""

import argparse
import os
import shutil
import subprocess
import sys
from typing import Mapping, Optional, Sequence

MIN_PYTHON = (3, 10)
REQUIRED_COMMANDS = ("git", "ffmpeg", "ffprobe")
GEMINI_KEY_NAMES = ("GEMINI_API_KEY", "GOOGLE_API_KEY")


def version_tuple(version_info: Optional[Sequence[int]] = None) -> tuple[int, int, int]:
    source = version_info if version_info is not None else sys.version_info
    values = list(source)
    return int(values[0]), int(values[1]), int(values[2] if len(values) > 2 else 0)


def python_status(version_info: Optional[Sequence[int]] = None) -> dict[str, object]:
    version = version_tuple(version_info)
    return {
        "ok": version[:2] >= MIN_PYTHON,
        "version": ".".join(str(part) for part in version),
        "minimum": ".".join(str(part) for part in MIN_PYTHON),
    }


def ensure_supported_python() -> None:
    status = python_status()
    if not status["ok"]:
        raise RuntimeError(
            f"Python {status['minimum']} 이상이 필요합니다. 현재 버전: {status['version']}"
        )


def command_status(name: str) -> dict[str, object]:
    executable = shutil.which(name)
    if not executable:
        return {"ok": False, "path": None, "version": None}
    version_flag = "-version" if name in {"ffmpeg", "ffprobe"} else "--version"
    try:
        result = subprocess.run(
            [executable, version_flag],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return {"ok": False, "path": executable, "version": "실행할 수 없음"}
    output = (result.stdout.strip() or result.stderr.strip()).splitlines()
    return {
        "ok": result.returncode == 0,
        "path": executable,
        "version": output[0] if output else "확인할 수 없음",
    }


def gemini_key_status(environ: Optional[Mapping[str, str]] = None) -> dict[str, object]:
    """키 값은 반환하지 않고, 사용할 환경변수 이름과 존재 여부만 반환한다."""

    values = environ if environ is not None else os.environ
    for name in GEMINI_KEY_NAMES:
        if str(values.get(name, "")).strip():
            return {"ok": True, "name": name}
    return {"ok": False, "name": None}


def print_key_status(environ: Optional[Mapping[str, str]] = None) -> int:
    status = gemini_key_status(environ)
    if status["ok"]:
        print(f"GEMINI_TTS_KEY=present ({status['name']})")
        return 0
    print("GEMINI_TTS_KEY=not-set")
    print("GEMINI_API_KEY 또는 GOOGLE_API_KEY를 현재 터미널에 등록해 주세요.")
    return 2


def print_environment_report(require_key: bool = False) -> int:
    python = python_status()
    python_ok = bool(python["ok"])
    print(f"PYTHON={'OK' if python_ok else 'FAIL'} version={python['version']} minimum={python['minimum']}")

    tools_ok = True
    for name in REQUIRED_COMMANDS:
        status = command_status(name)
        if status["ok"]:
            print(f"{name.upper()}=OK version={status['version']}")
        else:
            tools_ok = False
            print(f"{name.upper()}=MISSING install-required")

    key_status = gemini_key_status()
    key_ok = bool(key_status["ok"])
    if key_ok:
        print(f"GEMINI_TTS_KEY=present ({key_status['name']})")
    else:
        print("GEMINI_TTS_KEY=not-set")

    passed = python_ok and tools_ok and (key_ok or not require_key)
    print(f"ENV_CHECK={'pass' if passed else 'fail'}")
    if not python_ok:
        print("안내: references/environment-setup.md의 Python 설치 방법을 확인하세요.")
    if not tools_ok:
        print("안내: references/environment-setup.md의 Git·FFmpeg 설치 방법을 확인하세요.")
    if require_key and not key_ok:
        print("안내: Gemini API 키를 등록한 뒤 --check-key로 값이 아닌 등록 상태만 확인하세요.")
    return 0 if passed else 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="화이트보드 숏츠 필수 실행 환경 확인")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="Python·시스템 도구·키 상태 확인")
    action.add_argument("--check-key", action="store_true", help="Gemini 키 등록 여부만 확인")
    parser.add_argument("--require-key", action="store_true", help="전체 점검에서 Gemini 키를 필수로 확인")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.check_key:
        return print_key_status()
    return print_environment_report(require_key=args.require_key)


if __name__ == "__main__":
    raise SystemExit(main())
