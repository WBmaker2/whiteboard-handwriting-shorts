#!/usr/bin/env python3
from __future__ import annotations

import re
import struct
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_FILES = (
    "SKILL.md",
    "README.md",
    "LICENSE",
    "VERSION",
    "CHANGELOG.md",
    "THIRD_PARTY_NOTICES.md",
    "requirements-dev.txt",
    ".github/workflows/validate.yml",
    "assets/drawing-hand.png",
    "agents/openai.yaml",
    "references/environment-setup.md",
    "references/runtime-bootstrap.md",
    "references/third-party-notices.md",
    "references/licenses/HYPERFRAMES-APACHE-2.0.txt",
    "references/licenses/SRT-WHITEBOARD-ANIMATION-MIT.txt",
    "scripts/bootstrap_runtime.py",
    "scripts/check_environment.py",
    "scripts/environment_checks.py",
    "scripts/prepare_env.py",
    "scripts/test_environment_checks.py",
    "scripts/test_bootstrap_runtime.py",
)
OFFICIAL_URLS = (
    "https://github.com/heygen-com/hyperframes.git",
    "https://github.com/geeklee/srt-whiteboard-animation.git",
)
FORBIDDEN_PARTS = {".venv", "__pycache__", "output", "tmp"}
SECRET_PATTERNS = (
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"gh[opusr]_[A-Za-z0-9]{20,}"),
)


def fail(message: str) -> None:
    raise RuntimeError(message)


def validate_frontmatter() -> None:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        fail("SKILL.md YAML frontmatter가 없습니다.")
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        fail("SKILL.md frontmatter가 객체가 아닙니다.")
    if data.get("name") != "whiteboard-handwriting-shorts":
        fail("SKILL.md name이 올바르지 않습니다.")
    if not isinstance(data.get("description"), str) or not data["description"].strip():
        fail("SKILL.md description이 비어 있습니다.")


def validate_png() -> None:
    path = ROOT / "assets/drawing-hand.png"
    header = path.read_bytes()[:26]
    if len(header) < 26 or header[:8] != b"\x89PNG\r\n\x1a\n":
        fail("drawing-hand.png가 유효한 PNG가 아닙니다.")
    width, height, _depth, color_type = struct.unpack(">IIBB", header[16:26])
    if width < 1 or height < 1:
        fail("drawing-hand.png 크기가 올바르지 않습니다.")
    if color_type not in {4, 6}:
        fail("drawing-hand.png에 알파 채널이 없습니다.")


def validate_tree() -> None:
    missing = [item for item in REQUIRED_FILES if not (ROOT / item).is_file()]
    if missing:
        fail(f"필수 파일 누락: {', '.join(missing)}")

    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if FORBIDDEN_PARTS.intersection(relative.parts):
            fail(f"배포 제외 경로 포함: {relative}")
        if path.is_file() and path.suffix == ".py":
            line_count = len(path.read_text(encoding="utf-8").splitlines())
            if line_count > 500:
                fail(f"500줄을 초과한 Python 파일: {relative} ({line_count})")


def validate_sources_and_secrets() -> None:
    combined = "\n".join(
        (ROOT / name).read_text(encoding="utf-8")
        for name in ("SKILL.md", "README.md", "THIRD_PARTY_NOTICES.md")
    )
    for url in OFFICIAL_URLS:
        if url not in combined:
            fail(f"공식 출처 URL 누락: {url}")

    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                fail(f"비밀정보 형식이 감지됨: {path.relative_to(ROOT)}")


def main() -> int:
    try:
        validate_tree()
        validate_frontmatter()
        validate_png()
        validate_sources_and_secrets()
    except (OSError, RuntimeError, ValueError, yaml.YAMLError) as error:
        print(f"[error] {error}", file=sys.stderr)
        return 1
    print("distribution-validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
