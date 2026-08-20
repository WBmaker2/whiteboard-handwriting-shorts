#!/usr/bin/env python3
"""Prepare and validate the one-time runtime for whiteboard Shorts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime_sources import write_sources

SCHEMA_VERSION = 1
BOOTSTRAP_VERSION = "1.0.0"
SKILL_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_HAND = SKILL_ROOT / "assets/drawing-hand.png"
RUNTIME_ENV = "WHITEBOARD_SHORTS_RUNTIME_ROOT"
REPOSITORIES = {
    "hyperframes": {
        "url": "https://github.com/heygen-com/hyperframes.git",
        "directory": "hyperframes",
        "skipLfs": True,
    },
    "srt-whiteboard-animation": {
        "url": "https://github.com/geeklee/srt-whiteboard-animation.git",
        "directory": "srt-whiteboard-animation",
        "skipLfs": False,
    },
}


class SetupError(RuntimeError):
    pass


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def default_runtime_root() -> Path:
    override = os.environ.get(RUNTIME_ENV)
    if override:
        return Path(override).expanduser().resolve()
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library/Application Support/whiteboard-handwriting-shorts"
    if sys.platform.startswith("win"):
        local = os.environ.get("LOCALAPPDATA")
        return (Path(local) if local else home / "AppData/Local") / "whiteboard-handwriting-shorts"
    data_home = os.environ.get("XDG_DATA_HOME")
    return (Path(data_home) if data_home else home / ".local/share") / "whiteboard-handwriting-shorts"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="화이트보드 숏츠 최초 실행 환경 준비 및 검증")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true", help="상태를 읽기 전용으로 검증")
    action.add_argument("--plan", action="store_true", help="승인받을 설치 계획만 표시")
    action.add_argument("--apply", action="store_true", help="승인 후 최초 설치 실행")
    action.add_argument("--repair", action="store_true", help="승인 후 누락 자산 복구")
    parser.add_argument("--approved", action="store_true", help="현재 대화에서 사용자가 설치를 승인했음을 확인")
    parser.add_argument("--install-root", type=Path, help="저장소·자산·상태 파일을 둘 사용자 데이터 폴더")
    parser.add_argument(
        "--hand-variant",
        choices=("upstream", "no-text"),
        help="사용자가 승인한 손 이미지: 원본(upstream) 또는 글자 없는 수정본(no-text)",
    )
    return parser.parse_args()


def runtime_root(explicit: Path | None) -> Path:
    return explicit.expanduser().resolve() if explicit else default_runtime_root().resolve()


def expected_urls(hyperframes_url: str, srt_url: str) -> dict[str, str]:
    return {
        "hyperframes": hyperframes_url,
        "srt-whiteboard-animation": srt_url,
    }


def state_path(root: Path) -> Path:
    return root / "setup-state.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def png_info(path: Path) -> dict[str, Any]:
    header = path.read_bytes()[:26]
    if len(header) < 26 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise SetupError(f"PNG 파일이 아닙니다: {path}")
    width, height = struct.unpack(">II", header[16:24])
    color_type = header[25]
    return {
        "width": width,
        "height": height,
        "hasAlpha": color_type in {4, 6},
        "colorType": color_type,
    }


def command_version(name: str) -> dict[str, str] | None:
    executable = shutil.which(name)
    if not executable:
        return None
    result = subprocess.run(
        [executable, "--version"],
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    output = result.stdout.strip() or result.stderr.strip()
    return {"path": executable, "version": output.splitlines()[0] if output else "unknown"}


def run_git(arguments: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> str:
    git = shutil.which("git")
    if not git:
        raise SetupError("git을 찾지 못했습니다.")
    result = subprocess.run(
        [git, *arguments],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=900,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git 명령에 실패했습니다."
        raise SetupError(message)
    return result.stdout.strip()


def normalize_remote(value: str) -> str:
    stripped = value.strip().rstrip("/").removesuffix(".git")
    if "://" not in stripped and not stripped.startswith("git@"):
        return str(Path(stripped).expanduser().resolve()).rstrip("/")
    return stripped


def repository_path(root: Path, name: str) -> Path:
    return root / "repositories" / str(REPOSITORIES[name]["directory"])


def inspect_repository(path: Path, expected_url: str, expected_commit: str | None = None) -> tuple[list[str], dict[str, Any] | None]:
    reasons: list[str] = []
    if not path.is_dir() or not (path / ".git").is_dir():
        return [f"필수 저장소가 없습니다: {path}"], None
    try:
        remote = run_git(["remote", "get-url", "origin"], cwd=path)
        commit = run_git(["rev-parse", "HEAD"], cwd=path)
        dirty = bool(run_git(["status", "--porcelain"], cwd=path))
    except SetupError as exc:
        return [f"저장소를 확인할 수 없습니다: {path} ({exc})"], None
    if normalize_remote(remote) != normalize_remote(expected_url):
        reasons.append(f"origin URL이 예상과 다릅니다: {path}")
    if expected_commit and commit != expected_commit:
        reasons.append(f"설치 당시 커밋과 다릅니다: {path}")
    if dirty:
        reasons.append(f"저장소에 보존해야 할 로컬 변경이 있습니다: {path}")
    return reasons, {
        "url": expected_url,
        "path": str(path.resolve()),
        "commit": commit,
        "clean": not dirty,
    }


def clone_or_adopt(root: Path, name: str, url: str) -> dict[str, Any]:
    destination = repository_path(root, name)
    if destination.exists():
        reasons, snapshot = inspect_repository(destination, url)
        if reasons or snapshot is None:
            detail = "\n- ".join(reasons)
            raise SetupError(
                f"기존 폴더를 덮어쓰지 않습니다: {destination}\n- {detail}\n"
                "다른 --install-root를 선택하거나 기존 폴더를 직접 확인해 주세요."
            )
        return snapshot

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.parent / f".{destination.name}.clone-{uuid.uuid4().hex[:10]}"
    environment = os.environ.copy()
    if bool(REPOSITORIES[name]["skipLfs"]):
        environment["GIT_LFS_SKIP_SMUDGE"] = "1"
    try:
        run_git(["clone", "--depth", "1", url, str(temporary)], env=environment)
        temporary.replace(destination)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    reasons, snapshot = inspect_repository(destination, url)
    if reasons or snapshot is None:
        raise SetupError("복제한 저장소 검증에 실패했습니다: " + "; ".join(reasons))
    return snapshot


def prepare_hand_asset(root: Path, variant: str) -> dict[str, Any]:
    if variant == "no-text":
        source = CANONICAL_HAND
        source_note = "srt-whiteboard-animation 손 이미지에서 글자를 제거한 스킬 배포본"
    elif variant == "upstream":
        source = repository_path(root, "srt-whiteboard-animation") / "assets/drawing-hand.png"
        source_note = "srt-whiteboard-animation 공식 원본 저장소 자산"
    else:
        raise SetupError("손 이미지 종류를 upstream 또는 no-text 중에서 선택해야 합니다.")
    if not source.is_file():
        raise SetupError(f"선택한 손 이미지가 없습니다: {source}")
    source_info = png_info(source)
    if not source_info["hasAlpha"]:
        raise SetupError("선택한 손 이미지는 투명 PNG여야 합니다.")
    destination = root / "assets/drawing-hand.png"
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_hash = sha256(source)
    if destination.exists() and sha256(destination) != source_hash:
        backup_dir = root / "assets/backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
        backup = backup_dir / f"drawing-hand-{timestamp}.png"
        shutil.copy2(destination, backup)
    if not destination.exists() or sha256(destination) != source_hash:
        shutil.copy2(source, destination)
    runtime_info = png_info(destination)
    if not runtime_info["hasAlpha"] or sha256(destination) != source_hash:
        raise SetupError("런타임 손 이미지 검증에 실패했습니다.")
    return {
        "variant": variant,
        "source": str(source.resolve()),
        "sourceNote": source_note,
        "path": str(destination.resolve()),
        "sha256": source_hash,
        **runtime_info,
    }


def load_state(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.is_file():
        return None, [f"초기 설정 결과 파일이 없습니다: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"초기 설정 결과 파일을 읽을 수 없습니다: {exc}"]
    if not isinstance(data, dict):
        return None, ["초기 설정 결과 파일 형식이 잘못되었습니다."]
    return data, []


def inspect_runtime(root: Path, urls: dict[str, str]) -> tuple[bool, list[str], dict[str, Any] | None]:
    path = state_path(root)
    state, reasons = load_state(path)
    if state is None:
        return False, reasons, None
    if state.get("schemaVersion") != SCHEMA_VERSION:
        reasons.append("초기 설정 스키마 버전이 현재 스킬과 다릅니다.")
    if state.get("bootstrapVersion") != BOOTSTRAP_VERSION:
        reasons.append("초기 설정 버전이 현재 스킬과 다릅니다.")
    if state.get("status") != "ready":
        reasons.append("초기 설정 상태가 ready가 아닙니다.")
    if state.get("installRoot") != str(root.resolve()):
        reasons.append("기록된 설치 폴더가 현재 설치 폴더와 다릅니다.")
    expected_sources = root / "THIRD_PARTY_SOURCES.md"
    if state.get("sourcesFile") != str(expected_sources.resolve()) or not expected_sources.is_file():
        reasons.append("제3자 출처 기록 파일이 없거나 경로가 다릅니다.")

    tools = {name: command_version(name) for name in ("git", "ffmpeg", "ffprobe")}
    for name, detail in tools.items():
        if detail is None:
            reasons.append(f"필수 실행 도구가 없습니다: {name}")

    recorded_repositories = state.get("repositories", {})
    for name, url in urls.items():
        recorded = recorded_repositories.get(name, {}) if isinstance(recorded_repositories, dict) else {}
        recorded_commit = recorded.get("commit") if isinstance(recorded, dict) else None
        if recorded.get("url") != url:
            reasons.append(f"{name} 저장소 URL 기록이 현재 스킬과 다릅니다.")
        expected_repo_path = repository_path(root, name)
        if recorded.get("path") != str(expected_repo_path.resolve()):
            reasons.append(f"{name} 저장소 경로 기록이 현재 설치 경로와 다릅니다.")
        repo_reasons, _ = inspect_repository(expected_repo_path, url, recorded_commit)
        reasons.extend(repo_reasons)

    runtime_hand = root / "assets/drawing-hand.png"
    recorded_assets = state.get("assets", {})
    recorded_hand = recorded_assets.get("drawingHand", {}) if isinstance(recorded_assets, dict) else {}
    try:
        if recorded_hand.get("path") != str(runtime_hand.resolve()):
            reasons.append("손 이미지 경로 기록이 현재 설치 경로와 다릅니다.")
        variant = recorded_hand.get("variant")
        if variant == "no-text":
            expected_source = CANONICAL_HAND
        elif variant == "upstream":
            expected_source = repository_path(root, "srt-whiteboard-animation") / "assets/drawing-hand.png"
        else:
            raise SetupError("기록된 손 이미지 종류가 올바르지 않습니다.")
        expected_hash = sha256(expected_source)
        runtime_hash = sha256(runtime_hand)
        runtime_info = png_info(runtime_hand)
        if recorded_hand.get("sha256") != expected_hash or runtime_hash != expected_hash:
            reasons.append("손 이미지 체크섬이 승인된 이미지 기준과 다릅니다.")
        if not runtime_info["hasAlpha"]:
            reasons.append("런타임 손 이미지에 투명 알파 채널이 없습니다.")
    except (OSError, SetupError) as exc:
        reasons.append(f"런타임 손 이미지를 확인할 수 없습니다: {exc}")
    return not reasons, reasons, state


def project_runtime_snapshot(state: dict[str, Any]) -> dict[str, Any]:
    repositories = state.get("repositories", {})
    drawing_hand = state.get("assets", {}).get("drawingHand", {})
    return {
        "stateFile": state.get("stateFile"),
        "sourcesFile": state.get("sourcesFile"),
        "bootstrapVersion": state.get("bootstrapVersion"),
        "repositories": {
            name: {
                "url": detail.get("url"),
                "commit": detail.get("commit"),
            }
            for name, detail in repositories.items()
        },
        "drawingHand": {
            "variant": drawing_hand.get("variant"),
            "path": drawing_hand.get("path"),
            "sha256": drawing_hand.get("sha256"),
        },
    }


def require_ready_state(explicit_state: Path | None = None) -> dict[str, Any]:
    root = explicit_state.expanduser().resolve().parent if explicit_state else default_runtime_root().resolve()
    urls = expected_urls(REPOSITORIES["hyperframes"]["url"], REPOSITORIES["srt-whiteboard-animation"]["url"])
    ready, reasons, state = inspect_runtime(root, urls)
    if not ready or state is None:
        details = "\n- ".join(reasons)
        raise SetupError(
            "화이트보드 손그림 런타임 준비가 필요합니다.\n- "
            f"{details}\n먼저 `python {Path(__file__).resolve()} --plan`을 실행해 계획을 보여주고 "
            "사용자 승인을 받은 뒤 설치하세요."
        )
    return state


def print_plan(root: Path, urls: dict[str, str], hand_variant: str | None) -> None:
    ready, reasons, _ = inspect_runtime(root, urls)
    print("두 GitHub 저장소를 모두 내려받아야만 이 스킬로 손그림 동영상을 만들 수 있습니다.")
    print("설치 전 사용자에게 아래 네트워크 다운로드와 파일 생성을 설명하고 명시적 승인을 받아야 합니다.")
    print(f"INSTALL_ROOT={root}")
    print(f"STATE_FILE={state_path(root)}")
    print("필수 다운로드:")
    print(f"- HyperFrames 원본(heygen-com, Apache-2.0): {urls['hyperframes']} (Git LFS 대용량 테스트 파일 제외)")
    print(
        "- srt-whiteboard-animation 원본(geeklee, MIT): "
        f"{urls['srt-whiteboard-animation']}"
    )
    print("손 이미지 선택과 별도 승인도 필요합니다:")
    print("- upstream: 위 srt-whiteboard-animation 원본 저장소의 투명 손 이미지")
    print("- no-text: 원본 손 이미지에서 펜의 글자를 제거한 스킬 내장 투명 이미지(추천)")
    print(f"SELECTED_HAND_VARIANT={hand_variant or 'approval-required'}")
    print(f"- 승인된 손 이미지 준비 위치: {root / 'assets/drawing-hand.png'}")
    print(f"- 출처 기록 파일: {root / 'THIRD_PARTY_SOURCES.md'}")
    print("- 상태 파일에는 경로·커밋·체크섬·도구 버전만 기록하며 API 키는 기록하지 않습니다.")
    if ready:
        print("CURRENT_STATUS=ready")
    else:
        print("CURRENT_STATUS=setup-required")
        for reason in reasons:
            print(f"- {reason}")


def write_state(root: Path, data: dict[str, Any]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    destination = state_path(root)
    temporary = root / f".setup-state-{uuid.uuid4().hex}.tmp"
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(destination)
    return destination


def apply_setup(root: Path, urls: dict[str, str], hand_variant: str) -> dict[str, Any]:
    missing = [name for name in ("git", "ffmpeg", "ffprobe") if command_version(name) is None]
    if missing:
        raise SetupError("필수 실행 도구가 없습니다: " + ", ".join(missing))
    repositories = {name: clone_or_adopt(root, name, url) for name, url in urls.items()}
    hand = prepare_hand_asset(root, hand_variant)
    tools = {name: command_version(name) for name in ("git", "ffmpeg", "ffprobe", "node")}
    completed_at = now_iso()
    data = {
        "schemaVersion": SCHEMA_VERSION,
        "bootstrapVersion": BOOTSTRAP_VERSION,
        "status": "ready",
        "completedAt": completed_at,
        "lastVerifiedAt": completed_at,
        "installRoot": str(root.resolve()),
        "stateFile": str(state_path(root).resolve()),
        "sourcesFile": str((root / "THIRD_PARTY_SOURCES.md").resolve()),
        "approval": {
            "approved": True,
            "recordedAt": completed_at,
            "scope": [
                "clone-required-official-repositories",
                f"prepare-transparent-hand-asset:{hand_variant}",
            ],
        },
        "repositories": repositories,
        "assets": {"drawingHand": hand},
        "tools": {"python": {"path": sys.executable, "version": sys.version.split()[0]}, **tools},
    }
    write_sources(root, data)
    write_state(root, data)
    ready, reasons, state = inspect_runtime(root, urls)
    if not ready or state is None:
        raise SetupError("설치 후 검증에 실패했습니다: " + "; ".join(reasons))
    return state


def main() -> int:
    args = parse_args()
    root = runtime_root(args.install_root)
    urls = expected_urls(
        REPOSITORIES["hyperframes"]["url"],
        REPOSITORIES["srt-whiteboard-animation"]["url"],
    )
    if args.plan:
        print_plan(root, urls, args.hand_variant)
        return 0
    if args.check:
        ready, reasons, state = inspect_runtime(root, urls)
        if ready and state is not None:
            print("SETUP_READY=true")
            print(f"STATE_FILE={state_path(root)}")
            return 0
        print("SETUP_READY=false")
        for reason in reasons:
            print(f"- {reason}")
        return 2
    if not args.approved:
        print("사용자의 명시적 승인 후 --approved를 포함해 다시 실행해야 합니다.", file=sys.stderr)
        return 3
    if not args.hand_variant:
        print(
            "원본(upstream) 또는 글자 없는 수정본(no-text) 중 사용자가 승인한 손 이미지를 "
            "--hand-variant로 지정해야 합니다.",
            file=sys.stderr,
        )
        return 3
    try:
        state = apply_setup(root, urls, args.hand_variant)
    except SetupError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1
    print("SETUP_READY=true")
    print(f"STATE_FILE={state['stateFile']}")
    print(f"HYPERFRAMES_COMMIT={state['repositories']['hyperframes']['commit']}")
    print(f"SRT_WHITEBOARD_COMMIT={state['repositories']['srt-whiteboard-animation']['commit']}")
    print(f"DRAWING_HAND={state['assets']['drawingHand']['path']}")
    print(f"HAND_VARIANT={state['assets']['drawingHand']['variant']}")
    print(f"SOURCES_FILE={state['sourcesFile']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
