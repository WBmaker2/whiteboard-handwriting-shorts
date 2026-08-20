#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import os
import shutil
import subprocess
import sys
import time
import wave
from pathlib import Path

from environment_checks import ensure_supported_python

DEFAULT_MODEL = "gemini-3.1-flash-tts-preview"
DEFAULT_VOICE = "Vindemiatrix"
DEFAULT_STYLE = "초등학생에게 설명하는 친절하고 차분한 한국어 교사, 또박또박, 보통보다 약간 느리게, 과장 없이"


def build_prompt(script: str, style: str) -> str:
    return (
        "한국어 음성 합성을 수행하세요. 아래 지시문이나 구분 표시는 읽지 말고, "
        "낭독 원고의 문장만 정확히 말하세요.\n"
        f"말하기 스타일: {style}\n\n"
        "[낭독 원고 시작]\n"
        f"{script.strip()}\n"
        "[낭독 원고 끝]"
    )


def decode_audio_data(data: object) -> bytes:
    if isinstance(data, bytes):
        return data
    if isinstance(data, bytearray):
        return bytes(data)
    if isinstance(data, str):
        return base64.b64decode(data)
    raise TypeError(f"지원하지 않는 오디오 데이터 형식: {type(data).__name__}")


def write_wave(path: Path, pcm: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24000)
        wav_file.writeframes(pcm)


def convert_to_mp3(wav_path: Path, mp3_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("MP3 변환에는 시스템 ffmpeg가 필요합니다.")
    mp3_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(wav_path),
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(mp3_path),
        ],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "MP3 변환에 실패했습니다.")


def synthesize(prompt: str, model: str, voice: str, retries: int) -> bytes:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY 또는 GOOGLE_API_KEY가 설정되어 있지 않습니다.")

    from google import genai

    client = genai.Client(api_key=key)
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            interaction = client.interactions.create(
                model=model,
                input=prompt,
                response_format={"type": "audio"},
                generation_config={"speech_config": [{"voice": voice}]},
            )
            output_audio = interaction.output_audio
            if output_audio is None or not getattr(output_audio, "data", None):
                raise RuntimeError("Gemini 응답에 오디오 데이터가 없습니다.")
            return decode_audio_data(output_audio.data)
        except Exception as error:
            last_error = error
            if attempt < retries:
                time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(f"Gemini TTS 생성에 실패했습니다: {last_error}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="승인된 원고를 Gemini TTS 음성으로 생성")
    parser.add_argument("script", type=Path, help="UTF-8 낭독 원고 텍스트 파일")
    parser.add_argument("--wav", type=Path, required=True, help="WAV 출력 경로")
    parser.add_argument("--mp3", type=Path, help="선택 MP3 출력 경로")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--style", default=DEFAULT_STYLE)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true", help="API 호출 없이 입력과 설정만 검증")
    return parser.parse_args()


def main() -> int:
    try:
        ensure_supported_python()
    except RuntimeError as error:
        print(f"[error] {error}", file=sys.stderr)
        print("먼저 references/environment-setup.md의 Python 설치 방법을 확인하세요.", file=sys.stderr)
        return 2
    args = parse_args()
    if not args.script.is_file():
        print(f"[error] 원고 파일이 없습니다: {args.script}", file=sys.stderr)
        return 2
    script = args.script.read_text(encoding="utf-8").strip()
    if not script:
        print("[error] 원고가 비어 있습니다.", file=sys.stderr)
        return 2
    prompt = build_prompt(script, args.style)
    if args.dry_run:
        print(f"DRY_RUN=1 MODEL={args.model} VOICE={args.voice} SCRIPT_CHARS={len(script)}")
        return 0

    try:
        pcm = synthesize(prompt, args.model, args.voice, max(1, args.retries))
        write_wave(args.wav, pcm)
        if args.mp3:
            convert_to_mp3(args.wav, args.mp3)
    except Exception as error:
        print(f"[error] {error}", file=sys.stderr)
        return 1

    print(f"WAV={args.wav.resolve()}")
    if args.mp3:
        print(f"MP3={args.mp3.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
