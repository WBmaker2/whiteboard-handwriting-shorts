# 최초 실행 환경 준비 계약

## 목적

이 절차는 머신마다 한 번 수행한다. 다음 두 공식 원본 저장소와 승인된 투명 손 이미지가 모두
검증되어야 영상 프로젝트를 만들 수 있다.

| 구성요소 | 공식 원본 | 라이선스 |
|---|---|---|
| HyperFrames | `https://github.com/heygen-com/hyperframes.git` | Apache-2.0 |
| srt-whiteboard-animation | `https://github.com/geeklee/srt-whiteboard-animation.git` | MIT |

미러, 포크, 사용자가 제공하지 않은 다른 URL로 대체하지 않는다. HyperFrames는 소스만 사용하도록
Git LFS의 대용량 테스트 미디어 다운로드를 생략한다.

## 실행 흐름

### 1. 읽기 전용 확인

```bash
python <SKILL_DIR>/scripts/bootstrap_runtime.py --check
```

- 종료 코드 0과 `SETUP_READY=true`: 그대로 프로젝트 준비로 이동한다.
- 종료 코드 2 또는 `SETUP_READY=false`: 아래 계획과 승인 절차를 수행한다.

### 2. 계획 제시

사용자가 선택하기 전에는 손 이미지 종류를 지정하지 않고 실행해도 된다.

```bash
python <SKILL_DIR>/scripts/bootstrap_runtime.py --plan
```

사용자에게 반드시 다음 내용을 한 번에 보여준다.

- 두 공식 저장소를 모두 받아야만 손그림 동영상 제작을 진행할 수 있다는 점
- 각 저장소의 소유자, 공식 URL과 라이선스
- 설치 경로와 생성될 `setup-state.json`, `THIRD_PARTY_SOURCES.md`
- HyperFrames의 Git LFS 대용량 테스트 파일은 받지 않는다는 점
- 기존 저장소를 pull, reset, 삭제하거나 덮어쓰지 않는다는 점
- API 키와 토큰은 기록하지 않는다는 점
- 아래 손 이미지 두 종류의 차이

### 3. 손 이미지 선택

| 값 | 의미 | 처리 |
|---|---|---|
| `upstream` | srt-whiteboard-animation 공식 원본 손 이미지 | 원본 clone에서 런타임 자산 폴더로 복사 |
| `no-text` | 원본 손 이미지에서 펜의 글자를 제거한 투명 수정본 | 스킬의 `assets/drawing-hand.png`를 런타임 자산으로 복사 |

`no-text`를 추천할 수 있지만 자동 선택하지 않는다. “저장소 다운로드 승인”과 “선택한 손 이미지
승인”이 모두 명확한 답을 받은 경우에만 다음 단계로 진행한다.

승인 요청 예시:

> 손그림 동영상 제작을 위해 위 두 공식 GitHub 저장소를 표시된 경로에 내려받아도 될까요?
> 손 이미지는 원본 `upstream`과 펜 글자가 없는 `no-text` 중 어느 것을 승인하시겠습니까?

### 4. 승인 후 적용

```bash
python <SKILL_DIR>/scripts/bootstrap_runtime.py --plan --hand-variant no-text
python <SKILL_DIR>/scripts/bootstrap_runtime.py --apply --approved --hand-variant no-text
```

원본을 승인받았다면 `no-text` 대신 `upstream`을 쓴다. `--approved`는 실제 현재 대화에서
명시적 승인을 받은 뒤에만 사용한다.

적용 스크립트는 다음을 수행한다.

1. `git`, `ffmpeg`, `ffprobe` 존재 확인
2. 고정된 공식 URL에서 두 저장소 얕은 clone
3. `origin` URL, HEAD 커밋, 작업 폴더 변경 여부 확인
4. 승인된 손 이미지를 별도 런타임 폴더에 복사
5. PNG 크기·알파 채널·SHA-256 확인
6. 출처와 설치 커밋을 `THIRD_PARTY_SOURCES.md`에 기록
7. 준비 결과를 `setup-state.json`에 원자적으로 기록

### 5. 적용 후 재검증

```bash
python <SKILL_DIR>/scripts/bootstrap_runtime.py --check
```

재검증이 실패하면 콘텐츠 단계로 넘어가지 않는다.

## 다음 실행에서 건너뛰는 조건

`setup-state.json`이 있다는 사실만으로는 준비 완료로 인정하지 않는다. 다음 조건이 모두 맞아야 한다.

- 상태 스키마와 bootstrap 버전이 현재 스킬과 일치
- 두 저장소 폴더와 `.git` 존재
- 각 `origin`이 고정된 공식 URL과 일치
- 각 HEAD가 설치 당시 기록한 커밋과 일치
- 저장소에 보존해야 할 로컬 변경이 없음
- 승인된 손 이미지 SHA-256이 원본 또는 `no-text` 기준과 일치
- 손 이미지가 실제 알파 채널을 가진 PNG
- `THIRD_PARTY_SOURCES.md` 존재
- `git`, `ffmpeg`, `ffprobe` 사용 가능

## 변경 또는 손상 시 복구

`--check`가 실패하면 이유를 사용자에게 보여주고 복구 승인을 받는다.

```bash
python <SKILL_DIR>/scripts/bootstrap_runtime.py --plan --hand-variant <승인된 종류>
python <SKILL_DIR>/scripts/bootstrap_runtime.py --repair --approved --hand-variant <승인된 종류>
python <SKILL_DIR>/scripts/bootstrap_runtime.py --check
```

- 저장소가 없으면 공식 원본에서 다시 clone한다.
- 기존 저장소의 origin이 다르거나 로컬 변경이 있으면 자동 수정하지 않고 중단한다.
- 손 이미지가 다르면 기존 런타임 사본을 `assets/backups/`에 보존하고 승인된 이미지로 복구한다.
- 저장소 업데이트는 초기 설정 복구와 구분하며 자동 pull하지 않는다.

## 상태와 출처 파일

기본 위치는 운영체제별 사용자 데이터 폴더다. `--install-root`로 다른 위치를 승인받아 지정할 수
있다. 상태 파일에는 다음만 기록하며 비밀값은 기록하지 않는다.

- 설치·승인·검증 시각
- 공식 URL, 로컬 경로와 커밋 SHA
- 손 이미지 종류, 원본 설명, 경로, SHA-256, 크기와 알파 채널 여부
- Python, Git, FFmpeg 도구 경로와 버전

새 영상의 `project.json`에는 이 상태의 저장소 커밋과 손 이미지 체크섬을 스냅샷으로 남기고,
`THIRD_PARTY_SOURCES.md`를 프로젝트 `logs/runtime-sources.md`로 복사한다.
