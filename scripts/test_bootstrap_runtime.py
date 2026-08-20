#!/usr/bin/env python3
"""Offline integration test for bootstrap_runtime.py."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import bootstrap_runtime as bootstrap


def run(command: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)


def make_repository(root: Path, name: str, include_hand: bool = False) -> Path:
    repository = root / name
    repository.mkdir()
    run(["git", "init"], repository)
    run(["git", "config", "user.name", "Bootstrap Test"], repository)
    run(["git", "config", "user.email", "bootstrap-test@example.invalid"], repository)
    (repository / "README.md").write_text(f"# {name}\n", encoding="utf-8")
    if include_hand:
        assets = repository / "assets"
        assets.mkdir()
        shutil.copy2(bootstrap.CANONICAL_HAND, assets / "drawing-hand.png")
    run(["git", "add", "."], repository)
    run(["git", "commit", "-m", "test fixture"], repository)
    return repository


def verify_variant(sandbox: Path, urls: dict[str, str], variant: str) -> None:
    runtime = sandbox / f"runtime-{variant}"
    ready, reasons, _ = bootstrap.inspect_runtime(runtime, urls)
    assert not ready and reasons

    state = bootstrap.apply_setup(runtime, urls, variant)
    assert state["status"] == "ready"
    assert state["assets"]["drawingHand"]["variant"] == variant
    assert Path(state["sourcesFile"]).is_file()
    ready, reasons, _ = bootstrap.inspect_runtime(runtime, urls)
    assert ready, reasons

    hand = runtime / "assets/drawing-hand.png"
    hand.write_bytes(b"damaged test file")
    ready, reasons, _ = bootstrap.inspect_runtime(runtime, urls)
    assert not ready and any("손 이미지" in reason for reason in reasons)
    repaired = bootstrap.apply_setup(runtime, urls, variant)
    assert repaired["assets"]["drawingHand"]["sha256"] == bootstrap.sha256(hand)
    assert any((runtime / "assets/backups").glob("drawing-hand-*.png"))


def verify_project_initialization(sandbox: Path, sources: dict[str, Path]) -> None:
    runtime = sandbox / "runtime-official"
    official_urls = {
        name: str(bootstrap.REPOSITORIES[name]["url"])
        for name in bootstrap.REPOSITORIES
    }
    for name, source in sources.items():
        destination = bootstrap.repository_path(runtime, name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", str(source), str(destination)])
        run(["git", "remote", "set-url", "origin", official_urls[name]], destination)
    state = bootstrap.apply_setup(runtime, official_urls, "no-text")
    output_root = sandbox / "projects"
    environment = os.environ.copy()
    environment[bootstrap.RUNTIME_ENV] = str(runtime)
    initializer = Path(__file__).with_name("init_video_project.py")
    result = subprocess.run(
        [sys.executable, str(initializer), "--title", "bootstrap test", "--output-root", str(output_root)],
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    project_json = next(output_root.glob("*/project.json"))
    project = json.loads(project_json.read_text(encoding="utf-8"))
    assert project["runtimeSetup"]["repositories"]["hyperframes"]["commit"]
    assert project["runtimeSetup"]["drawingHand"]["variant"] == "no-text"
    assert (project_json.parent / "logs/runtime-sources.md").is_file()
    assert state["sourcesFile"]


def main() -> int:
    if not all(shutil.which(tool) for tool in ("git", "ffmpeg", "ffprobe")):
        raise RuntimeError("테스트에 git, ffmpeg, ffprobe가 필요합니다.")
    with tempfile.TemporaryDirectory(prefix="whiteboard-bootstrap-test-") as temporary:
        sandbox = Path(temporary)
        hyperframes = make_repository(sandbox, "hyperframes-source")
        srt = make_repository(sandbox, "srt-source", include_hand=True)
        urls = {
            "hyperframes": str(hyperframes),
            "srt-whiteboard-animation": str(srt),
        }
        output = StringIO()
        with redirect_stdout(output):
            bootstrap.print_plan(sandbox / "plan-only", urls, None)
        assert "두 GitHub 저장소를 모두" in output.getvalue()
        assert not (sandbox / "plan-only").exists()
        verify_variant(sandbox, urls, "no-text")
        verify_variant(sandbox, urls, "upstream")
        verify_project_initialization(
            sandbox,
            {"hyperframes": hyperframes, "srt-whiteboard-animation": srt},
        )
    print("bootstrap-runtime-tests: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
