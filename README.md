# whiteboard-handwriting-shorts

사용자가 제공한 자료를 바탕으로 사실 확인, 기획, 자막 원고, 화면 구성, 손그림 이미지, Gemini TTS, 최종 세로형 영상까지 제작하도록 안내하는 Codex 스킬입니다.

이 스킬은 콘텐츠 제작의 여섯 단계와 최초 실행 환경 준비를 모두 사용자 승인 게이트로 관리합니다. 승인 전에는 다음 단계 생성이나 외부 API 호출을 진행하지 않습니다.

## 주요 기능

- 약 1분 길이의 한국어 교육용 세로형 숏츠 제작
- 10개 아이디어부터 최종 영상까지 단계별 사용자 승인
- 영상별 독립 프로젝트 폴더와 `project.json` 승인 기록
- 1080×1920 화이트보드 손그림 애니메이션
- Gemini TTS 한국어 나레이션과 SRT 자막
- 공식 원본 저장소와 손 이미지 체크섬을 기록하는 최초 실행 검증
- 원본 손 이미지 또는 no-text 손 이미지 선택 승인

## 설치

### Git으로 설치

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/WBmaker2/whiteboard-handwriting-shorts.git \
  ~/.codex/skills/whiteboard-handwriting-shorts
```

### GitHub Release로 설치

최신 Release에서 `whiteboard-handwriting-shorts-v*.zip`을 내려받고 압축을 풀어 다음 폴더에 놓습니다.

```text
~/.codex/skills/whiteboard-handwriting-shorts/
```

설치 후 Codex를 다시 시작하거나 스킬 목록을 새로고침합니다.

## 필수 최초 실행 준비

손그림 동영상을 만들려면 아래 두 공식 원본 저장소가 모두 필요합니다.

1. [HeyGen HyperFrames](https://github.com/heygen-com/hyperframes) — Apache-2.0
2. [geeklee srt-whiteboard-animation](https://github.com/geeklee/srt-whiteboard-animation) — MIT

스킬은 미러나 포크 주소를 받지 않습니다. 최초 실행 시 다운로드 계획과 설치 위치를 먼저 보여주고 사용자가 승인한 뒤에만 공식 URL에서 clone합니다.

```bash
python scripts/bootstrap_runtime.py --check
python scripts/bootstrap_runtime.py --plan --hand-variant no-text
python scripts/bootstrap_runtime.py --apply --approved --hand-variant no-text
python scripts/bootstrap_runtime.py --check
```

`no-text`는 추천 선택지일 뿐 자동 선택되지 않습니다. 사용자는 공식 원본의 `upstream` 손 이미지와 스킬에 포함된 `no-text` 수정본 중 하나를 명시적으로 승인해야 합니다.

## 사용 방법

Codex에서 자료와 함께 다음처럼 요청합니다.

```text
$whiteboard-handwriting-shorts를 사용해 이 자료로 1분 교육용 화이트보드 숏츠를 만들어 주세요.
```

스킬은 다음 순서마다 결과를 제시하고 승인을 기다립니다.

```text
최초 환경 준비 승인
  → 아이디어 승인
  → 자막 원고 승인
  → 장면 구성 승인
  → 손그림 이미지 승인
  → TTS 음성 승인
  → 최종 영상 승인
```

자세한 운영 규칙은 [SKILL.md](SKILL.md), 최초 실행 절차는 [references/runtime-bootstrap.md](references/runtime-bootstrap.md)를 확인하세요.

운영체제별 Python·Git·FFmpeg 설치, Gemini API 키 발급, 환경변수 등록, 비밀값을 출력하지 않는 확인 명령,
설치 실패 재시도 절차는 [references/environment-setup.md](references/environment-setup.md)에 정리했습니다.

## 요구 환경

- Python 3.10 이상
- Git
- FFmpeg와 FFprobe
- 영상 렌더링용 Python 패키지: `opencv-python`, `numpy`, `av`, `Pillow`
- Gemini TTS 사용 시 `google-genai`와 `GEMINI_API_KEY` 또는 `GOOGLE_API_KEY`

실행 전 Python과 시스템 도구를 확인합니다. Python 3.10 미만이거나 Git·FFmpeg·FFprobe가 없으면 공식 설치
안내를 확인한 뒤 다시 점검합니다. macOS/Linux에서 `python` 명령이 없으면 아래 명령의 `python`을 `python3`로,
Windows PowerShell에서는 `py`로 바꿔 실행합니다.

```bash
python scripts/check_environment.py --check
```

필요한 Python 패키지는 계획을 먼저 확인하고 사용자 승인 후 스킬 전용 `.venv`에 준비합니다.

```bash
python scripts/prepare_env.py --check
python scripts/prepare_env.py --plan
python scripts/prepare_env.py --apply --approved
python scripts/prepare_env.py --check
```

Gemini TTS를 사용할 때는 [Google AI Studio API Keys](https://aistudio.google.com/apikey)에서 키를 발급하고
`GEMINI_API_KEY` 또는 `GOOGLE_API_KEY`로 등록합니다. 키를 출력하지 않고 등록 여부만 확인하려면 다음을
실행합니다.

```bash
python scripts/check_environment.py --check-key
```

API 키는 저장소나 산출물에 기록하지 마세요.

## 테스트

```bash
python -m compileall -q scripts
uv run --with ruff ruff check --select E4,E7,E9,F,I scripts
python scripts/check_environment.py --check
python scripts/test_environment_checks.py
python scripts/test_bootstrap_runtime.py
uv run --with pyyaml python scripts/validate_distribution.py
```

자세한 내용은 [TESTING.md](TESTING.md)를 확인하세요.

## 출처와 라이선스

- 이 저장소의 자체 작성 코드는 [MIT License](LICENSE)로 배포합니다.
- 제3자 저장소와 수정 손 이미지의 출처는 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)에 명시했습니다.
- 전체 제3자 라이선스 원문은 [references/licenses](references/licenses)에 보존합니다.
- `assets/drawing-hand.png`는 `srt-whiteboard-animation`의 MIT 라이선스 손 이미지를 바탕으로 펜의 글자를 제거한 no-text 수정본입니다.

HyperFrames와 srt-whiteboard-animation 자체는 이 저장소에 포함하지 않으며, 사용자가 최초 실행에서 승인한 경우에만 각각의 공식 저장소에서 내려받습니다.

## English summary

This Codex skill builds fact-checked Korean educational vertical whiteboard Shorts with a mandatory first-run setup approval and six content approval gates. See the Korean sections above and [SKILL.md](SKILL.md) for the complete workflow.
