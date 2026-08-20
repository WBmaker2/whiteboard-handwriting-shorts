#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from bootstrap_runtime import SetupError, project_runtime_snapshot, require_ready_state
from environment_checks import ensure_supported_python

SUBDIRECTORIES = (
    "input",
    "research",
    "planning",
    "prompts",
    "images",
    "regions",
    "audio",
    "scenes",
    "captions",
    "previews/final-checks",
    "logs",
    "final",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="새 화이트보드 숏츠용 독립 프로젝트 폴더 생성")
    parser.add_argument("--title", required=True, help="영상 프로젝트 제목")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("output/educational-whiteboard"),
        help="영상별 폴더를 만들 상위 디렉터리",
    )
    parser.add_argument("--slug", help="폴더명에 사용할 슬러그")
    parser.add_argument("--source", action="append", default=[], help="원자료 파일, 폴더 또는 URL")
    parser.add_argument("--date", help="YYYYMMDD 형식 날짜. 생략하면 오늘 날짜")
    parser.add_argument("--dry-run", action="store_true", help="폴더를 만들지 않고 예정 경로만 표시")
    parser.add_argument("--setup-state", type=Path, help="기본 위치가 아닌 setup-state.json 경로")
    return parser.parse_args()


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().lower()
    normalized = re.sub(r"[^\w가-힣]+", "-", normalized, flags=re.UNICODE)
    normalized = re.sub(r"[_-]+", "-", normalized).strip("-")
    return normalized[:60].rstrip("-") or "video"


def validate_date(value: str | None, now: datetime) -> str:
    if value is None:
        return now.strftime("%Y%m%d")
    parsed = datetime.strptime(value, "%Y%m%d")
    return parsed.strftime("%Y%m%d")


def unique_directory(base: Path) -> Path:
    if not base.exists():
        return base
    for number in range(2, 1000):
        candidate = base.with_name(f"{base.name}-{number:02d}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"고유 프로젝트 폴더명을 만들 수 없습니다: {base}")


def unique_file(directory: Path, name: str) -> Path:
    target = directory / name
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    for number in range(2, 1000):
        candidate = directory / f"{stem}-{number:02d}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"고유 파일명을 만들 수 없습니다: {target}")


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def copy_sources(project_root: Path, sources: list[str], checked_at: str) -> list[dict[str, str]]:
    input_dir = project_root / "input"
    entries: list[dict[str, str]] = []
    for source in sources:
        if is_url(source):
            entries.append(
                {"kind": "url", "original": source, "stored": "source-index.md", "checkedAt": checked_at}
            )
            continue
        path = Path(source).expanduser().resolve()
        if path.is_file():
            destination = unique_file(input_dir, path.name)
            shutil.copy2(path, destination)
            entries.append(
                {
                    "kind": "file",
                    "original": str(path),
                    "stored": destination.relative_to(project_root).as_posix(),
                    "checkedAt": checked_at,
                }
            )
        elif path.is_dir():
            entries.append(
                {
                    "kind": "directory-indexed",
                    "original": str(path),
                    "stored": "source-index.md",
                    "checkedAt": checked_at,
                }
            )
        else:
            entries.append(
                {
                    "kind": "unavailable",
                    "original": source,
                    "stored": "source-index.md",
                    "checkedAt": checked_at,
                }
            )
    return entries


def write_source_index(path: Path, entries: list[dict[str, str]]) -> None:
    lines = [
        "# 원자료 목록",
        "",
        "| 구분 | 원본 위치 | 프로젝트 내 사본·기록 | 확인 시각 |",
        "|---|---|---|---|",
    ]
    if not entries:
        lines.append("| 없음 | 사용자가 대화로 제공한 자료 | 대화 내용을 기획 문서에 요약 | - |")
    for entry in entries:
        values = [
            entry["kind"],
            entry["original"],
            entry["stored"],
            entry["checkedAt"],
        ]
        escaped = [value.replace("|", "\\|").replace("\n", " ") for value in values]
        lines.append(f"| {' | '.join(escaped)} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    try:
        ensure_supported_python()
    except RuntimeError as error:
        print(f"[error] {error}")
        print("먼저 references/environment-setup.md의 Python 설치 방법을 확인하세요.")
        return 2
    args = parse_args()
    now = datetime.now().astimezone()
    date_prefix = validate_date(args.date, now)
    slug = slugify(args.slug or args.title)
    output_root = args.output_root.expanduser().resolve()
    project_root = unique_directory(output_root / f"{date_prefix}-{slug}")

    if args.dry_run:
        print(f"PROJECT_ROOT={project_root}")
        return 0

    try:
        runtime_state = require_ready_state(args.setup_state)
    except SetupError as exc:
        print(f"[error] {exc}")
        return 2

    for relative in SUBDIRECTORIES:
        (project_root / relative).mkdir(parents=True, exist_ok=False)

    created_at = now.isoformat(timespec="seconds")
    sources = copy_sources(project_root, args.source, created_at)
    write_source_index(project_root / "input/source-index.md", sources)
    runtime_sources = Path(str(runtime_state["sourcesFile"]))
    shutil.copy2(runtime_sources, project_root / "logs/runtime-sources.md")

    project = {
        "projectId": project_root.name,
        "title": args.title,
        "createdAt": created_at,
        "projectRoot": ".",
        "status": "planning",
        "sourceIndex": "input/source-index.md",
        "fps": 24,
        "width": 1080,
        "height": 1920,
        "audio": "audio/voiceover.mp3",
        "output": f"final/{slug}-shorts.mp4",
        "runtimeSetup": project_runtime_snapshot(runtime_state),
        "approvals": {
            stage: {"approved": False, "approvedAt": None}
            for stage in ("ideas", "script", "storyboard", "images", "voice", "final")
        },
        "scenes": [],
    }
    project_json = project_root / "project.json"
    project_json.write_text(
        json.dumps(project, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (project_root / "logs/project-created.txt").write_text(
        f"createdAt={created_at}\nprojectRoot={project_root}\nsourceCount={len(sources)}\n"
        f"runtimeState={runtime_state['stateFile']}\nruntimeSources=logs/runtime-sources.md\n",
        encoding="utf-8",
    )
    print(f"PROJECT_ROOT={project_root}")
    print(f"PROJECT_JSON={project_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
