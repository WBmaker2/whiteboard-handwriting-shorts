# Security Policy

## Secrets

Gemini API 키는 `GEMINI_API_KEY` 또는 `GOOGLE_API_KEY` 환경변수로만 제공합니다. 키를 이 저장소, 영상 프로젝트, 로그, 이슈 또는 테스트 파일에 기록하지 마세요.
발급과 운영체제별 등록 방법은 [실행 환경 안내](references/environment-setup.md)를 따르고, 등록 확인에는 키 값을
출력하지 않는 `python scripts/check_environment.py --check-key`를 사용하세요.

## Dependency bootstrap

이 스킬은 최초 실행에서 사용자 승인을 받은 후 다음 공식 저장소만 clone합니다.

- https://github.com/heygen-com/hyperframes.git
- https://github.com/geeklee/srt-whiteboard-animation.git

저장소 origin, 커밋, 작업 트리와 손 이미지 체크섬이 기록과 다르면 자동 복구하지 않고 다시 승인을 요구합니다.

## Reporting

보안 문제를 발견했다면 공개 이슈에 비밀정보를 포함하지 말고 GitHub 저장소의 비공개 보안 권고 기능을 사용해 주세요.
