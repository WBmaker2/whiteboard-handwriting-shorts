# whiteboard-handwriting-shorts GitHub 공개 배포 계획

## 목표

- 정제된 `whiteboard-handwriting-shorts` 스킬만 별도 공개 저장소에 배포한다.
- 제작 과정에서 생성된 영상, 음성, 원자료, 로컬 가상환경과 API 키는 포함하지 않는다.
- 설치 방법, 필수 원본 저장소, 제3자 라이선스와 손 이미지 출처를 명확히 표시한다.
- 최초 버전 `1.0.0.0`을 GitHub Release ZIP과 SHA-256 파일로 제공한다.

## 공개 저장소

- 소유자: `WBmaker2`
- 저장소: `whiteboard-handwriting-shorts`
- 공개 범위: Public
- 기본 브랜치: `main`
- 배포 방식: GitHub 저장소 + GitHub Release

## 포함 범위

- `SKILL.md`, `agents/`, `assets/`, `references/`, `scripts/`
- `README.md`, `LICENSE`, `CHANGELOG.md`, `VERSION`
- 설치 및 테스트 안내
- GitHub Actions 검증 워크플로
- 이 배포 계획 문서

## 제외 범위

- 영상별 `output/`과 `tmp/`
- Gemini·ElevenLabs 등 API 키와 `.env*`
- `.venv/`, `__pycache__/`, `.DS_Store`
- 로컬에 별도로 내려받은 HyperFrames 및 srt-whiteboard-animation 저장소

## 출처 정책

- HyperFrames는 `https://github.com/heygen-com/hyperframes.git`만 허용한다.
- srt-whiteboard-animation은 `https://github.com/geeklee/srt-whiteboard-animation.git`만 허용한다.
- 두 저장소는 스킬 실행 중 사용자 승인 후 별도 런타임 폴더에 clone하며 이 저장소에 재배포하지 않는다.
- 내장 `assets/drawing-hand.png`는 srt-whiteboard-animation의 MIT 라이선스 손 이미지를 수정한 no-text 파생본으로 고지한다.

## 검증 및 배포 순서

1. 정제된 스킬 패키지를 새 로컬 저장소에 복사한다.
2. 비밀정보, 대용량 산출물, 중첩 저장소가 없는지 검사한다.
3. Python 컴파일, bootstrap 통합 테스트, 스킬 구조 검증을 실행한다.
4. 배포 문서와 라이선스를 검토한다.
5. `main`에 최초 커밋하고 공개 GitHub 저장소를 생성해 푸시한다.
6. GitHub Actions 성공을 확인한다.
7. `v1.0.0.0` 태그와 ZIP·SHA-256 자산을 포함한 GitHub Release를 생성한다.
8. 저장소와 Release URL을 다시 열어 공개 상태와 자산을 확인한다.
