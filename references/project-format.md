# 영상별 프로젝트 폴더와 렌더링 계약

## 목차

- 새 영상과 기존 영상 구분
- 머신별 최초 실행 준비
- 프로젝트 초기화
- 폴더 구조
- project.json
- regions JSON
- 장면 렌더링
- 최종 합성
- Gemini TTS

## 새 영상과 기존 영상 구분

- 새 주제, 새 버전, 새 납품본을 제작하면 새 프로젝트 폴더를 만든다.
- 기존 영상 수정은 사용자가 계속 작업할 프로젝트의 project.json을 지정하거나 기존 경로가 확실히 확인된 경우에만 같은 폴더에서 수행한다.
- 이름이 겹치면 접미사를 붙인다. 기존 폴더를 비우거나 덮어쓰지 않는다.

## 머신별 최초 실행 준비

프로젝트 폴더를 만들기 전에 `scripts/bootstrap_runtime.py --check`가 `SETUP_READY=true`를
반환해야 한다. 준비 상태에는 heygen-com/HyperFrames와 geeklee/srt-whiteboard-animation의
공식 원본 clone, 설치 커밋, 사용자가 승인한 손 이미지와 출처 기록이 모두 포함된다.
자세한 승인·설치·복구 절차는 [runtime-bootstrap.md](runtime-bootstrap.md)를 따른다.

## 프로젝트 초기화

작업을 시작하기 전에 실행한다.

~~~bash
python <SKILL_DIR>/scripts/init_video_project.py \
  --title "광복절 계기교육" \
  --source "/path/to/source.md" \
  --source "https://example.org/reference"
~~~

기본 생성 위치는 현재 작업공간의 output/educational-whiteboard/이다. 명령은 다음 값을 출력한다.

~~~text
PROJECT_ROOT=/absolute/path/output/educational-whiteboard/20260820-광복절-계기교육
PROJECT_JSON=/absolute/path/output/educational-whiteboard/20260820-광복절-계기교육/project.json
~~~

이후 작업은 PROJECT_ROOT 안에서만 수행한다. 다른 출력 루트가 필요하면 --output-root로 명시한다.

## 폴더 구조

~~~text
output/educational-whiteboard/YYYYMMDD-<slug>/
  project.json
  input/
    source-index.md
    <복사한 원자료>
  research/
    sources.md
    fact-check.md
  planning/
    01-ideas.md
    02-script.md
    03-storyboard.md
    narration.txt
  prompts/
    image-prompts.md
    tts-prompt.md
  images/
    scene-01.png ... scene-10.png
  regions/
    scene-01.json ... scene-10.json
  audio/
    voiceover.wav
    voiceover.mp3
  scenes/
    scene-01.mp4 ... scene-10.mp4
  captions/
    caption-01.png ... caption-10.png
  previews/
    images-contact-sheet.png
    final-checks/
  logs/
    project-created.txt
    runtime-sources.md
    05-tts-validation.txt
    06-media-validation.txt
  final/
    <slug>-shorts.mp4
    <slug>-shorts.srt
~~~

로컬 원자료 파일은 input/에 복사한다. URL, 폴더, 접근할 수 없는 자료는 input/source-index.md에 원본 위치와 확인 시간을 기록한다. 비밀키와 토큰은 어떤 파일에도 기록하지 않는다.

## project.json

모든 상대 경로는 project.json이 있는 폴더를 기준으로 해석한다.

~~~json
{
  "projectId": "20260820-sample-topic",
  "title": "샘플 주제",
  "createdAt": "2026-08-20T12:00:00+09:00",
  "projectRoot": ".",
  "fps": 24,
  "width": 1080,
  "height": 1920,
  "audio": "audio/voiceover.mp3",
  "output": "final/sample-topic-shorts.mp4",
  "runtimeSetup": {
    "stateFile": "/user-data/whiteboard-handwriting-shorts/setup-state.json",
    "sourcesFile": "/user-data/whiteboard-handwriting-shorts/THIRD_PARTY_SOURCES.md",
    "bootstrapVersion": "1.0.0",
    "repositories": {
      "hyperframes": {"url": "https://github.com/heygen-com/hyperframes.git", "commit": "<SHA>"},
      "srt-whiteboard-animation": {
        "url": "https://github.com/geeklee/srt-whiteboard-animation.git",
        "commit": "<SHA>"
      }
    },
    "drawingHand": {"variant": "no-text", "path": "/runtime/assets/drawing-hand.png", "sha256": "<SHA-256>"}
  },
  "approvals": {
    "ideas": {"approved": false, "approvedAt": null},
    "script": {"approved": false, "approvedAt": null},
    "storyboard": {"approved": false, "approvedAt": null},
    "images": {"approved": false, "approvedAt": null},
    "voice": {"approved": false, "approvedAt": null},
    "final": {"approved": false, "approvedAt": null}
  },
  "scenes": [
    {
      "id": "scene-01",
      "image": "images/scene-01.png",
      "regions": "regions/scene-01.json",
      "video": "scenes/scene-01.mp4",
      "startMs": 0,
      "endMs": 4500,
      "subtitle": "첫 장면의 승인된 자막"
    }
  ]
}
~~~

scenes는 최종 합성 전에 정확히 10개가 되어야 한다. 시간은 겹치지 않고 0부터 오름차순으로 이어지며 마지막 endMs는 승인된 음성 길이와 대체로 일치해야 한다.

## regions JSON

이미지 원본 픽셀 좌표를 사용하고 화면 구성표의 그려지는 순서대로 배열한다.

~~~json
{
  "regions": [
    {"label": "배경 지도", "x": 120, "y": 260, "width": 820, "height": 760},
    {"label": "주인공", "x": 300, "y": 900, "width": 480, "height": 620}
  ]
}
~~~

영역이 없으면 렌더러는 전체 이미지를 한 영역으로 사용한다.

## 장면 렌더링

PROJECT_ROOT에서 실행하며 장면 길이는 endMs - startMs로 계산한다.

~~~bash
<ENV_PY> <SKILL_DIR>/scripts/render_whiteboard_scene.py \
  images/scene-01.png scenes/scene-01.mp4 \
  --duration-ms 4500 \
  --regions-json regions/scene-01.json \
  --hand "<DRAWING_HAND>" \
  --width 1080 --height 1920 --fps 24
~~~

## 최종 합성

~~~bash
<ENV_PY> <SKILL_DIR>/scripts/build_vertical_short.py --project project.json
~~~

스크립트는 장면을 합치고, 오디오 길이에 맞춰 영상 속도를 미세 조정하고, 투명 PNG 자막을 직접 합성하며, final/에 MP4와 SRT를 출력한다. 시스템 ffmpeg와 ffprobe가 필요하다.

## Gemini TTS

~~~bash
<ENV_PY> <SKILL_DIR>/scripts/generate_gemini_tts.py planning/narration.txt \
  --wav audio/voiceover.wav \
  --mp3 audio/voiceover.mp3 \
  --voice Vindemiatrix \
  --style "초등학생에게 설명하는 친절하고 차분한 한국어 교사, 또박또박, 약간 느리게"
~~~

모델명이 더 이상 유효하지 않으면 Google의 공식 Gemini TTS 문서를 확인한 뒤 --model로 지원 모델을 지정한다.
