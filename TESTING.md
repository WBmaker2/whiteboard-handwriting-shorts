# Testing

## 목표

배포본이 비밀정보나 실행 산출물을 포함하지 않고, 최초 실행 승인 게이트와 공식 출처 검증을 유지하는지 확인합니다.

## 로컬 검증

Python 문법 검사:

```bash
python -m compileall -q scripts
uv run --with ruff ruff check --select E4,E7,E9,F,I scripts
```

실행 환경과 Python 최소 버전 점검:

```bash
python scripts/check_environment.py --check
python scripts/test_environment_checks.py
```

Gemini API 키가 없는 CI·공유 환경에서도 `--check`는 실행할 수 있습니다. TTS 직전에만 다음 명령으로 등록
여부를 확인하며, 실제 키 값은 출력하지 않습니다.

```bash
python scripts/check_environment.py --check-key
```

네트워크를 사용하지 않는 bootstrap 통합 테스트:

```bash
python scripts/test_bootstrap_runtime.py
```

배포 패키지 구조와 출처 검사:

```bash
uv run --with pyyaml python scripts/validate_distribution.py
```

Codex 스킬 구조 검사기를 사용할 수 있는 환경에서는 다음도 실행합니다.

```bash
uv run --with pyyaml python \
  ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

## 테스트 원칙

- 테스트는 실제 외부 GitHub 저장소를 변경하거나 API를 호출하지 않습니다.
- bootstrap 테스트는 임시 로컬 Git 저장소와 임시 런타임 폴더만 사용합니다.
- 실제 최초 다운로드와 손 이미지 교체는 반드시 사용자의 명시적 승인 후 수행합니다.
- API 키나 토큰을 테스트 fixture에 넣지 않습니다.
- 환경 점검 테스트는 가짜 키 문자열이 출력되지 않는지 확인합니다.
- `prepare_env.py --apply`는 `--approved` 없이는 가상환경을 만들거나 패키지를 설치하지 않습니다.
