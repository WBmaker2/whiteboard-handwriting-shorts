#!/usr/bin/env python3
"""환경 점검과 비밀값 비노출 규칙을 검증하는 오프라인 테스트."""

import os
import subprocess
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import environment_checks as checks


def test_python_versions() -> None:
    assert not checks.python_status((3, 9, 18))["ok"]
    assert checks.python_status((3, 10, 0))["ok"]
    assert checks.python_status((3, 12, 4))["ok"]
    assert not checks.command_status("command-that-does-not-exist-for-whiteboard-tests")["ok"]


def test_key_is_never_printed() -> None:
    secret = "test-secret-value-that-must-not-appear"
    output = StringIO()
    with redirect_stdout(output):
        result = checks.print_key_status({"GEMINI_API_KEY": secret})
    assert result == 0
    assert "present" in output.getvalue()
    assert secret not in output.getvalue()

    output = StringIO()
    with redirect_stdout(output):
        result = checks.print_key_status({})
    assert result == 2
    assert output.getvalue().splitlines()[0] == "GEMINI_TTS_KEY=not-set"

    script = Path(__file__).with_name("check_environment.py")
    environment = os.environ.copy()
    environment.pop("GOOGLE_API_KEY", None)
    environment["GEMINI_API_KEY"] = secret
    result = subprocess.run(
        [sys.executable, str(script), "--check-key"],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "GEMINI_TTS_KEY=present" in result.stdout
    assert secret not in result.stdout


def test_prepare_env_requires_approval() -> None:
    script = Path(__file__).with_name("prepare_env.py")
    result = subprocess.run(
        [sys.executable, str(script), "--apply"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 3
    assert "--approved" in result.stderr


def main() -> int:
    test_python_versions()
    test_key_is_never_printed()
    test_prepare_env_requires_approval()
    print("environment-check-tests: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
