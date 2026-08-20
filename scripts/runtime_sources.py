"""Write human-readable provenance for the runtime dependencies."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_sources(root: Path, data: dict[str, Any]) -> Path:
    repositories = data["repositories"]
    hand = data["assets"]["drawingHand"]
    destination = root / "THIRD_PARTY_SOURCES.md"
    lines = [
        "# Whiteboard Handwriting Shorts - Third-party Sources",
        "",
        f"- 설치 및 검증 시각: `{data['completedAt']}`",
        "- 아래 저장소는 표시된 공식 원본 URL의 `origin`과 설치 커밋을 검증했습니다.",
        "",
        "## HyperFrames",
        "",
        f"- 공식 원본: {repositories['hyperframes']['url']}",
        f"- 설치 커밋: `{repositories['hyperframes']['commit']}`",
        "- 라이선스: Apache-2.0",
        "- 라이선스 원문: https://github.com/heygen-com/hyperframes/blob/main/LICENSE",
        "",
        "## srt-whiteboard-animation",
        "",
        f"- 공식 원본: {repositories['srt-whiteboard-animation']['url']}",
        f"- 설치 커밋: `{repositories['srt-whiteboard-animation']['commit']}`",
        "- 라이선스: MIT",
        "- 라이선스 원문: https://github.com/geeklee/srt-whiteboard-animation/blob/main/LICENSE",
        "",
        "## Drawing hand asset",
        "",
        f"- 승인된 종류: `{hand['variant']}`",
        f"- 설명: {hand['sourceNote']}",
        f"- SHA-256: `{hand['sha256']}`",
        f"- 런타임 파일: `{hand['path']}`",
        "- 파생 출처: https://github.com/geeklee/srt-whiteboard-animation/tree/main/assets",
        "- 적용 라이선스: MIT",
        "",
        "원본 Git 저장소는 수정하지 않습니다. `no-text` 선택 시 수정본은 별도 런타임 자산으로만 사용합니다.",
    ]
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination
