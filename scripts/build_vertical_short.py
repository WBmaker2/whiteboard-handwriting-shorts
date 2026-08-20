#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from bootstrap_runtime import SetupError, require_ready_state
from PIL import Image, ImageDraw, ImageFont

APPROVAL_KEYS = ("ideas", "script", "storyboard", "images", "voice")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="10개 화이트보드 장면, 자막, TTS를 세로형 MP4로 합성")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--font", type=Path)
    parser.add_argument("--setup-state", type=Path, help="기본 위치가 아닌 setup-state.json 경로")
    return parser.parse_args()


def run(command: list[str]) -> None:
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "명령 실행에 실패했습니다.")


def probe_duration(path: Path) -> float:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("시스템 ffprobe가 필요합니다.")
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"재생 시간을 확인할 수 없습니다: {path}")
    return float(result.stdout.strip())


def resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else base / path


def validate_project(project: dict, base: Path) -> tuple[list[dict], Path, Path, int, int, int]:
    scenes = project.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != 10:
        raise ValueError("project.json의 scenes는 정확히 10개여야 합니다.")
    approvals = project.get("approvals", {})
    missing_approval = [
        key
        for key in APPROVAL_KEYS
        if not isinstance(approvals.get(key), dict) or not approvals[key].get("approved")
    ]
    if missing_approval:
        raise ValueError(f"승인되지 않은 단계가 있습니다: {', '.join(missing_approval)}")

    previous_end = 0
    for index, scene in enumerate(scenes, start=1):
        start = int(scene.get("startMs", -1))
        end = int(scene.get("endMs", -1))
        if start < 0 or end <= start or start < previous_end:
            raise ValueError(f"{index}번 장면의 시간이 잘못되었거나 겹칩니다.")
        if not str(scene.get("subtitle", "")).strip():
            raise ValueError(f"{index}번 장면 자막이 비어 있습니다.")
        video = resolve(base, str(scene.get("video", "")))
        if not video.is_file():
            raise FileNotFoundError(f"{index}번 장면 영상이 없습니다: {video}")
        previous_end = end

    audio = resolve(base, str(project.get("audio", "")))
    output = resolve(base, str(project.get("output", "")))
    if not audio.is_file():
        raise FileNotFoundError(f"음성 파일이 없습니다: {audio}")
    if not str(project.get("output", "")).strip():
        raise ValueError("project.json에 output 경로가 필요합니다.")
    width = int(project.get("width", 1080))
    height = int(project.get("height", 1920))
    fps = int(project.get("fps", 24))
    if width < 2 or height < 2 or fps < 1:
        raise ValueError("width, height, fps 값을 확인하세요.")
    return scenes, audio, output, width, height, fps


def choose_font(explicit: Path | None) -> Path:
    candidates = []
    if explicit:
        candidates.append(explicit)
    candidates.extend(
        [
            Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
            Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
            Path("/System/Library/AssetsV2/com_apple_MobileAsset_Font8/7a0b5c0f3c1d41c4c52a33343496c9c65ad52c50.asset/AssetData/NanumGothic.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
            Path("C:/Windows/Fonts/malgun.ttf"),
        ]
    )
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError("한글 자막 글꼴을 찾지 못했습니다. --font로 지정하세요.")


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    box = draw.textbbox((0, 0), text, font=font, stroke_width=2)
    return box[2] - box[0]


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if text_width(draw, candidate, font) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        if text_width(draw, word, font) <= max_width:
            current = word
            continue
        piece = ""
        for char in word:
            candidate_piece = piece + char
            if piece and text_width(draw, candidate_piece, font) > max_width:
                lines.append(piece)
                piece = char
            else:
                piece = candidate_piece
        current = piece
    if current:
        lines.append(current)
    return lines or [text]


def create_caption(
    path: Path,
    text: str,
    width: int,
    height: int,
    font_path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font_size = max(30, int(width * 0.052))
    font = ImageFont.truetype(str(font_path), font_size, index=0)
    lines = wrap_text(draw, text, font, width - int(width * 0.14))
    line_height = int(font_size * 1.35)
    padding_x = int(width * 0.035)
    padding_y = int(font_size * 0.48)
    text_h = line_height * len(lines) - int(font_size * 0.25)
    widest = max(text_width(draw, line, font) for line in lines)
    box_w = min(width - int(width * 0.05), widest + padding_x * 2)
    box_h = text_h + padding_y * 2
    box_x = (width - box_w) // 2
    bottom_safe = int(height * 0.095)
    box_y = height - bottom_safe - box_h
    draw.rounded_rectangle(
        (box_x, box_y, box_x + box_w, box_y + box_h),
        radius=max(14, int(width * 0.018)),
        fill=(18, 18, 18, 210),
        outline=(255, 255, 255, 90),
        width=max(2, width // 540),
    )
    y = box_y + padding_y
    for line in lines:
        line_w = text_width(draw, line, font)
        x = (width - line_w) // 2
        draw.text(
            (x, y),
            line,
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=2,
            stroke_fill=(0, 0, 0, 255),
        )
        y += line_height
    image.save(path)


def srt_time(seconds: float) -> str:
    milliseconds = max(0, int(round(seconds * 1000)))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_srt(output: Path, scenes: list[dict], timing_scale: float, audio_duration: float) -> Path:
    srt_path = output.with_suffix(".srt")
    blocks = []
    for index, scene in enumerate(scenes, start=1):
        start = int(scene["startMs"]) / 1000 * timing_scale
        end = int(scene["endMs"]) / 1000 * timing_scale
        if index == len(scenes):
            end = audio_duration
        blocks.append(
            f"{index}\n{srt_time(start)} --> {srt_time(end)}\n"
            f"{str(scene['subtitle']).strip()}\n"
        )
    srt_path.write_text("\n".join(blocks), encoding="utf-8")
    return srt_path


def concat_scenes(ffmpeg: str, scene_paths: list[Path], output: Path, fps: int) -> None:
    list_path = output.with_suffix(".txt")
    lines = []
    for path in scene_paths:
        escaped = path.resolve().as_posix().replace("'", r"'\\''")
        lines.append(f"file '{escaped}'")
    list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        run(
            [
                ffmpeg,
                "-y",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_path),
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "20",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(fps),
                str(output),
            ]
        )
    finally:
        list_path.unlink(missing_ok=True)


def compose(
    ffmpeg: str,
    merged: Path,
    captions: list[Path],
    timings: list[tuple[float, float]],
    audio: Path,
    output: Path,
    width: int,
    height: int,
    fps: int,
    audio_duration: float,
) -> None:
    merged_duration = probe_duration(merged)
    speed_ratio = audio_duration / merged_duration
    command = [ffmpeg, "-y", "-loglevel", "error", "-i", str(merged)]
    for caption in captions:
        command.extend(["-loop", "1", "-framerate", str(fps), "-i", str(caption)])
    command.extend(["-i", str(audio)])

    filters = [
        (
            f"[0:v]setpts=PTS*{speed_ratio:.9f},"
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=#F5EBD7[base]"
        )
    ]
    previous = "base"
    for index, (start, end) in enumerate(timings, start=1):
        output_label = f"o{index}"
        filters.append(
            f"[{previous}][{index}:v]overlay=0:0:"
            f"enable='between(t,{start:.3f},{end:.3f})'[{output_label}]"
        )
        previous = output_label
    audio_index = len(captions) + 1
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            f"[{previous}]",
            "-map",
            f"{audio_index}:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(fps),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-t",
            f"{audio_duration:.3f}",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    run(command)


def main() -> int:
    args = parse_args()
    try:
        require_ready_state(args.setup_state)
    except SetupError as error:
        print(f"[error] {error}", file=sys.stderr)
        return 2
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("[error] 시스템 ffmpeg가 필요합니다.", file=sys.stderr)
        return 1
    try:
        project_path = args.project.resolve()
        project = json.loads(project_path.read_text(encoding="utf-8"))
        base = project_path.parent
        scenes, audio, output, width, height, fps = validate_project(project, base)
        output.parent.mkdir(parents=True, exist_ok=True)
        font_path = choose_font(args.font)
        audio_duration = probe_duration(audio)
        last_end = int(scenes[-1]["endMs"]) / 1000
        if last_end <= 0:
            raise ValueError("마지막 장면의 endMs가 잘못되었습니다.")
        timing_scale = audio_duration / last_end

        captions_dir = base / "captions"
        captions = []
        timings = []
        for index, scene in enumerate(scenes, start=1):
            caption_path = captions_dir / f"caption-{index:02d}.png"
            create_caption(caption_path, str(scene["subtitle"]), width, height, font_path)
            captions.append(caption_path)
            start = int(scene["startMs"]) / 1000 * timing_scale
            end = int(scene["endMs"]) / 1000 * timing_scale
            if index == len(scenes):
                end = audio_duration
            timings.append((start, end))

        with tempfile.TemporaryDirectory(prefix="whiteboard-shorts-") as temp_dir:
            merged = Path(temp_dir) / "merged-silent.mp4"
            scene_paths = [resolve(base, str(scene["video"])) for scene in scenes]
            concat_scenes(ffmpeg, scene_paths, merged, fps)
            compose(
                ffmpeg,
                merged,
                captions,
                timings,
                audio,
                output,
                width,
                height,
                fps,
                audio_duration,
            )
        srt_path = write_srt(output, scenes, timing_scale, audio_duration)
        final_duration = probe_duration(output)
    except Exception as error:
        print(f"[error] {error}", file=sys.stderr)
        return 1

    print(f"OUTPUT={output.resolve()}")
    print(f"SRT={srt_path.resolve()}")
    print(f"DURATION={final_duration:.3f}")
    print(f"RESOLUTION={width}x{height} FPS={fps}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
