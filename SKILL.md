---
name: whiteboard-handwriting-shorts
description: "Create a fact-checked Korean educational vertical whiteboard Shorts video from user-provided materials, with a one-time approved runtime setup and six mandatory content approval gates. Use when a user asks to turn documents, notes, links, images, or research into a Shorts, Reels, TikTok-style, whiteboard, or hand-drawn explainer video."
---

# Whiteboard Handwriting Shorts

제공 자료를 사실 확인된 약 1분 분량의 세로형 교육 영상으로 완성한다. 사용자가 다른 언어를 요구하지 않는 한 모든 대화와 산출물을 한국어로 작성한다.

## 0단계: 최초 실행 환경 준비

영상 아이디어나 프로젝트 폴더를 만들기 전에 [최초 실행 준비 절차](references/runtime-bootstrap.md)를 읽고 다음 검사를 실행한다.

```bash
python <SKILL_DIR>/scripts/bootstrap_runtime.py --check
```

`SETUP_READY=true`이면 기록된 저장소·커밋·손 이미지·출처 파일이 다시 검증된 것이므로 추가 승인 없이 프로젝트 준비로 넘어간다. 준비되지 않았으면 다음 원칙을 모두 지킨다.

1. 아래 두 GitHub 공식 원본 저장소를 **모두 내려받아야만 이 스킬로 손그림 동영상을 만들 수 있다**고 사용자에게 명확히 안내한다.
   - `https://github.com/heygen-com/hyperframes.git` — heygen-com 공식 원본, Apache-2.0
   - `https://github.com/geeklee/srt-whiteboard-animation.git` — geeklee 공식 원본, MIT
2. 대체 미러·포크·압축 사본은 사용하지 않는다. 설치 후 각 저장소의 `origin`과 커밋 SHA를 검증한다.
3. `--plan`을 실행해 공식 출처, 설치 경로, 네트워크 다운로드, 생성 파일을 사용자에게 보여준다. 승인 전에는 clone, 패키지 설치, 자산 복사를 실행하지 않는다.
4. 손 이미지는 다음 두 선택지를 제시하고 사용자의 의견과 명시적 승인을 받는다. 추천은 가능하지만 자동 선택하지 않는다.
   - `upstream`: srt-whiteboard-animation 공식 원본의 투명 손 이미지
   - `no-text`: 원본 손 이미지에서 펜의 글자를 제거한 스킬 내장 투명 이미지
5. 사용자가 저장소 다운로드와 손 이미지 종류를 모두 승인하면 승인된 종류를 명시해 실행한다.

```bash
python <SKILL_DIR>/scripts/bootstrap_runtime.py --plan --hand-variant <upstream|no-text>
python <SKILL_DIR>/scripts/bootstrap_runtime.py --apply --approved --hand-variant <upstream|no-text>
python <SKILL_DIR>/scripts/bootstrap_runtime.py --check
```

6. 성공하면 운영체제별 사용자 데이터 폴더의 `setup-state.json`과 `THIRD_PARTY_SOURCES.md`를 근거로 남긴다. 이후 실행은 파일 존재만 보지 않고 공식 URL·커밋·경로·손 이미지 체크섬·투명도까지 확인한다.
   배포 시에는 [제3자 구성요소 고지](references/third-party-notices.md)와 `references/licenses/`를 함께 포함한다.
7. 누락·변경·손상이 발견되면 자동으로 pull, reset, 삭제, 덮어쓰지 않는다. 변경 내용과 복구 계획을 보여주고 다시 승인받은 뒤 `--repair --approved --hand-variant <승인된 종류>`를 실행한다.
8. 사용자가 필수 다운로드를 승인하지 않으면 손그림 동영상 제작을 시작하지 않는다. 0단계 승인은 머신별 환경 승인으로, 아래 콘텐츠 1~6단계 승인과 별개다.

## 승인 게이트 불변 규칙

1. 아래 1~6단계를 순서대로 수행한다.
2. 각 단계의 산출물을 사용자에게 보여준 뒤 반드시 멈추고 명시적 승인을 기다린다.
3. `승인`, `확정`, `진행`, `좋아요`처럼 현재 단계 결과를 수락하는 답만 승인으로 인정한다. 이전 단계의 승인, 최초의 포괄적 제작 요청, 무응답은 승인으로 간주하지 않는다.
4. 승인 전에는 다음 단계의 산출물을 만들거나 외부 생성 API를 호출하지 않는다.
5. 수정 요청이 오면 현재 단계만 고치고 다시 승인을 받는다. 상위 산출물이 바뀌어 영향을 받는 하위 산출물은 재승인 또는 재생성한다.
6. 각 승인 상태와 승인 시각을 프로젝트의 `project.json`에 기록한다.
7. 6단계 영상도 사용자가 최종 승인해야 완료로 표시한다.

## 영상별 독립 프로젝트 폴더 불변 규칙

1. 새로운 영상을 만들 때는 조사나 아이디어 작성을 시작하기 전에 전용 프로젝트 폴더를 하나 생성한다.
2. 기본 폴더명은 `output/educational-whiteboard/YYYYMMDD-<주제-slug>/`로 한다. 같은 이름이 있으면 `-02`, `-03`을 붙이고 기존 폴더나 파일을 덮어쓰지 않는다.
3. 원자료, 조사 기록, 승인 전후 기획안, 생성 프롬프트, 이미지, 음성, 장면 영상, 자막, 미리보기, 검증 로그, 최종 MP4와 SRT를 모두 해당 프로젝트 폴더 안에 저장한다. 스킬 자체의 실행 환경과 재사용 자산 외에는 프로젝트 폴더 밖에 중간 산출물을 만들지 않는다.
4. 제공받은 로컬 원자료는 이동하지 말고 `input/`에 복사한다. 링크와 복사할 수 없는 자료는 `input/source-index.md`에 원본 위치와 확인 날짜를 기록한다.
5. 사용자가 기존 영상의 수정이나 계속 작업을 명시하고 기존 `project.json` 경로가 확인된 경우에만 그 폴더를 재사용한다. 그 외에는 같은 주제라도 새 폴더를 만든다.
6. 각 단계의 산출물 경로는 `project.json`이 있는 프로젝트 루트를 기준으로 기록한다.

## 프로젝트 준비

0단계 검사를 통과한 새 영상이면 [references/project-format.md](references/project-format.md)를 읽고 프로젝트 폴더를 초기화한다. 초기화 스크립트는 준비 상태가 유효하지 않으면 폴더를 만들지 않는다.

```bash
python <SKILL_DIR>/scripts/init_video_project.py \
  --title "<영상 제목>" \
  --source "<제공 자료 경로 또는 URL>"
```

명령이 출력한 `PROJECT_ROOT`를 이번 영상의 유일한 작업 루트로 사용한다. 이후 모든 상대 경로는 이 폴더를 기준으로 해석하고, 사용자에게 단계 결과를 전달할 때도 이 폴더 안의 파일만 연결한다.

사실 주장, 날짜, 인물, 통계가 포함된 교육 자료는 공신력 있는 1차·공식 출처로 확인한다. 출처와 확인 내용을 `research/sources.md`와 `research/fact-check.md`에 저장하고 아이디어·스크립트 문서에서 참조한다. 추정이나 논쟁적 해석은 사실처럼 단정하지 않는다.

## 1단계: 영상 아이디어 10개

입력 자료를 읽고 교육 목표, 대상 학년, 핵심 사실, 오해 가능성을 정리한다. 서로 구별되는 아이디어를 정확히 10개 제안한다. 각 아이디어에 다음을 포함한다.

- 제목과 한 문장 훅
- 학습 목표
- 1분 안에 전달할 핵심 흐름
- 예상되는 10장면 구성
- 사실 확인이 필요한 지점과 활용 출처
- 화이트보드 손그림 영상에 적합한 이유

비교 가능한 표로 작성해 `planning/01-ideas.md`에 저장한다. 추천 아이디어 하나와 추천 이유를 덧붙이되 자동으로 선택하지 않는다. 사용자에게 번호 선택과 1단계 승인을 요청하고 멈춘다.

## 2단계: 1분 자막 스크립트

승인된 아이디어 하나만 사용한다. 약 45~60초, 기본 10장면의 한국어 내레이션·자막 스크립트를 작성한다. 초등 교육 영상이라면 짧은 문장, 쉬운 낱말, 정확한 인과관계를 사용한다.

장면별로 장면 번호, 예상 시간, 내레이션, 화면 자막을 표로 작성한다. 자막은 모바일에서 한눈에 읽히도록 한 화면 1~2줄로 제한한다. 마지막에는 전체 낭독문을 별도로 제공한다. `planning/02-script.md`와 순수 원고 `planning/narration.txt`에 저장한다.

사실·날짜·고유명사와 총 예상 시간을 다시 확인한 뒤 사용자에게 전체 스크립트 승인을 요청하고 멈춘다.

## 3단계: 10장면 화면 구성표

승인된 스크립트를 정확히 10개 장면으로 설계한다. 각 행에 다음 열을 포함해 `planning/03-storyboard.md`로 저장한다.

| 장면 | 시간 | 내레이션·자막 | 화면 구도 | 주요 손그림 요소 | 그려지는 순서 | 전환·움직임 | 사실·주의점 |
|---|---:|---|---|---|---|---|---|

세로 9:16 안전 영역을 고려해 핵심 대상은 중앙 80%에 두고, 하단 자막 영역과 앱 UI가 가릴 상·하단을 비운다. 한 장면에는 핵심 메시지 하나만 둔다. 사용자에게 표 전체의 승인을 요청하고 멈춘다.

## 4단계: 일관된 손그림 이미지 10장

4단계 시작 전 0단계 상태를 다시 확인한다. 두 공식 GitHub 저장소가 모두 준비되지 않았다면 사용자에게 해당 저장소를 내려받아야만 손그림 동영상을 만들 수 있다고 다시 안내하고 0단계로 돌아간다.

승인된 화면 구성표를 기준으로 이미지 생성 도구를 사용해 장면별 PNG를 정확히 10장 생성한다. 먼저 아래 공통 스타일 블록을 확정하고 모든 프롬프트에 문자 그대로 반복한다.

> Vertical 9:16 educational whiteboard illustration, warm ivory paper background, clean dark-gray hand-drawn line art, minimal flat accent colors limited to muted red, blue, and warm orange, generous negative space, calm friendly elementary-school tone, consistent character proportions and line weight across the entire ten-image series, no photorealism, no 3D, no gradients, no dense background, no readable text, letters, numbers, labels, logos, or watermarks.

기본 크기는 1080×1920 또는 도구가 지원하는 가장 가까운 9:16 비율로 한다. 첫 이미지를 스타일 기준으로 삼고 이후 장면에 같은 인물 설계, 선 굵기, 종이색, 제한 색상을 유지한다. 생성 후 실제 이미지를 열어 다음을 검사한다.

- 10장 모두 세로형이며 장면 내용이 구성표와 일치하는가
- 이미지 속 글자·숫자·워터마크가 없는가
- 역사 상징과 깃발 등 사실 요소가 왜곡되지 않았는가
- 핵심 대상이 하단 자막 영역과 겹치지 않는가
- 열 장의 화풍이 한 시리즈처럼 일관적인가

공통 스타일과 장면별 생성 프롬프트를 `prompts/image-prompts.md`에 저장한다. 이미지는 `images/scene-01.png`부터 `scene-10.png`로 저장하고 `previews/images-contact-sheet.png` 연락판과 개별 링크를 보여준다. 사용자에게 10장 전체의 승인을 요청하고 멈춘다.

## 5단계: Gemini TTS 내레이션

승인된 `planning/narration.txt`만 낭독시킨다. 사용자가 지정하지 않으면 차분하고 친절한 한국어 교사 톤, 보통보다 약간 느린 속도, 과장 없는 감정으로 지시한다. `GEMINI_API_KEY` 또는 `GOOGLE_API_KEY`를 사용하고 키를 출력하거나 파일에 저장하지 않는다.

먼저 환경을 준비한 뒤 TTS 스크립트를 실행한다.

```bash
python <SKILL_DIR>/scripts/prepare_env.py
<ENV_PY> <SKILL_DIR>/scripts/generate_gemini_tts.py planning/narration.txt --wav audio/voiceover.wav --mp3 audio/voiceover.mp3
```

오디오 길이, 코덱, 샘플레이트와 생성 설정을 `logs/05-tts-validation.txt`에 기록하되 API 키는 기록하지 않는다. 목표 45~60초를 벗어나면 원고를 몰래 고치지 말고 조정안을 제안한다. 원고가 바뀌면 2단계 승인을 다시 받고, 영향받은 3단계와 이후 단계를 갱신한다. 음성 파일을 재생 가능하게 보여주고 사용자에게 음색·속도·발음 승인을 요청한 뒤 멈춘다.

## 6단계: 자막·손그림 애니메이션 최종 영상

승인된 이미지와 음성만 사용한다. 각 이미지에서 주요 요소의 실제 픽셀 영역을 확인하고 장면의 이야기 순서대로 `regions`를 기록한다. 승인된 오디오의 문장 경계 또는 묵음 구간을 기준으로 10개 장면의 `startMs`와 `endMs`를 정해 `project.json`을 완성한다.

각 장면을 렌더링하고 최종 영상을 합성한다.

```bash
<ENV_PY> <SKILL_DIR>/scripts/render_whiteboard_scene.py images/scene-01.png scenes/scene-01.mp4 \
  --duration-ms 4500 --regions-json regions/scene-01.json --hand "<DRAWING_HAND>"

<ENV_PY> <SKILL_DIR>/scripts/build_vertical_short.py --project project.json
```

나머지 9개 장면도 같은 방식으로 렌더링한다. 최종 자막은 영상에 직접 합성하고 SRT도 함께 저장한다. 다음을 검증한다.

- 1080×1920, 9:16, 24fps, H.264 영상과 AAC 음성
- 전체 길이 약 45~60초, 음성 시작·끝 잘림 없음
- 10개 장면 순서와 자막 시간이 승인된 스크립트와 일치
- 손이 현재 그려지는 위치를 따라가고 마지막에 완성 그림이 보임
- 시작·중간·끝 표본 프레임에 검은 화면, 잘린 자막, 잘못된 장면이 없음

시작·중간·끝 표본 프레임을 `previews/final-checks/`에 저장하고 매체 검사 결과를 `logs/06-media-validation.txt`에 기록한다. 최종 MP4, SRT, 검증 결과를 사용자에게 보여주고 6단계 최종 승인을 요청한다. 승인 후에만 프로젝트를 완료로 표시한다.

## 변경 처리

- 1단계 변경: 2~6단계를 다시 수행한다.
- 2단계 원고 변경: 2단계를 재승인하고 3단계 타이밍을 갱신한다. 장면 의미가 바뀌면 4단계 이미지도 다시 승인받는다.
- 3단계 구성 변경: 영향받은 4단계 이미지와 6단계 영상을 다시 만든다.
- 4단계 이미지 변경: 해당 장면과 6단계 영상만 다시 만든다.
- 5단계 음성 변경: 자막 타이밍과 6단계 영상을 다시 만든다.
- 6단계 수정: 승인된 상위 산출물을 유지하고 합성·애니메이션만 다시 렌더링한다.
