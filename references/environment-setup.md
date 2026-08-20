# 실행 환경 준비 안내

이 문서는 스킬을 처음 실행하는 사용자가 필요한 프로그램과 Gemini TTS 인증을 준비하는 방법을 설명합니다.
스킬은 운영체제의 Python·Git·FFmpeg를 대신 설치하지 않습니다. 설치 계획과 Python 패키지 적용은 사용자에게
먼저 보여주고 승인받습니다.

아래 명령의 `python`은 macOS/Linux에서 `python` 명령이 없으면 `python3`로 바꿔 실행합니다. Windows
PowerShell에서는 `py`를 사용할 수 있습니다.

## 전체 흐름

```text
공식 설치
  → 새 터미널 열기
  → Python·Git·FFmpeg·FFprobe 사전 점검
  → (필요할 때) 패키지 설치 계획 확인
  → 사용자 승인
  → 스킬 전용 .venv에 패키지 적용
  → Gemini 키 등록 상태 확인
  → 영상 제작 단계 시작
```

## 1. 사전 점검

스킬 저장소 루트에서 실행합니다.

```bash
python scripts/check_environment.py --check
```

Windows에서 `python` 명령이 연결되지 않으면 다음처럼 실행할 수 있습니다.

```powershell
py scripts\check_environment.py --check
```

다음 항목을 확인합니다.

- Python 3.10 이상
- `git`
- `ffmpeg`
- `ffprobe` (`ffmpeg` 설치에 함께 포함되는 명령)
- Gemini 키 등록 여부(값은 출력하지 않음)

종료 코드가 2여도 화면에 누락 항목과 다음 안내 위치가 표시됩니다. 누락 항목을 설치한 뒤 새 터미널에서 같은
점검을 다시 실행합니다.

## 2. macOS 설치

### Homebrew 사용(권장)

[Homebrew 공식 사이트](https://brew.sh/)의 안내를 확인한 뒤 터미널에서 실행합니다.

```bash
brew install python@3.12 git ffmpeg
```

설치 확인:

```bash
python3 --version
git --version
ffmpeg -version
ffprobe -version
```

`python3 --version`이 3.10 미만이면 [Python 공식 다운로드 페이지](https://www.python.org/downloads/macos/)에서
3.10 이상을 설치합니다. Homebrew 또는 설치 프로그램이 PATH를 바꾼 뒤에는 터미널을 새로 열어야 합니다.

### 공식 Python 설치 프로그램 사용

[Python 공식 macOS 다운로드 페이지](https://www.python.org/downloads/macos/)에서 3.10 이상 설치 프로그램을
받아 설치합니다. Git과 FFmpeg는 [Git 공식 다운로드 페이지](https://git-scm.com/downloads) 및
[FFmpeg 공식 다운로드 페이지](https://ffmpeg.org/download.html)의 macOS 안내를 사용합니다.

## 3. Windows 설치

1. [Python 공식 Windows 다운로드 페이지](https://www.python.org/downloads/windows/)에서 Python 3.10 이상을
   설치합니다. 설치 화면에서 `Add python.exe to PATH`를 선택합니다.
2. [Git 공식 Windows 다운로드 페이지](https://git-scm.com/download/win)에서 Git for Windows를 설치합니다.
3. [FFmpeg 공식 다운로드 페이지](https://ffmpeg.org/download.html)의 `Windows EXE Files` 링크에서 Windows 빌드를
   내려받습니다. 압축을 예를 들어 `C:\Tools\ffmpeg`에 풀고, 사용자 `Path`에
   `C:\Tools\ffmpeg\bin`을 추가합니다.
4. PowerShell을 새로 열어 다음을 확인합니다.

```powershell
py --version
git --version
ffmpeg -version
ffprobe -version
```

FFmpeg 공식 페이지는 Windows용 실행 파일을 제공하는 빌드 배포처를 연결합니다. 출처가 불분명한 압축 파일 대신
공식 다운로드 페이지에서 연결한 빌드를 사용하세요.

## 4. Linux 설치

Ubuntu/Debian 계열의 예시는 다음과 같습니다.

```bash
sudo apt update
sudo apt install -y python3 python3-venv git ffmpeg
```

설치 확인:

```bash
python3 --version
git --version
ffmpeg -version
ffprobe -version
```

배포판의 Python이 3.10 미만이면 해당 배포판의 공식 Python 설치 문서를 확인하세요. 시스템 Python을 지우거나
교체하지 말고, 3.10 이상 인터프리터를 설치한 뒤 점검 명령에서 그 인터프리터를 사용합니다.

## 5. Gemini API 키 발급

발급 페이지: [Google AI Studio API Keys](https://aistudio.google.com/apikey)

공식 설명: [Gemini API 키 사용 안내](https://ai.google.dev/gemini-api/docs/api-key)

발급 순서:

1. 발급 페이지에 Google 계정으로 로그인합니다.
2. 약관 동의 또는 프로젝트 선택 화면이 나오면 안내에 따라 기본 프로젝트를 만들거나 기존 Google Cloud
   프로젝트를 가져옵니다.
3. `Create API key`를 선택합니다.
4. 생성된 키를 복사합니다. 키는 비밀번호처럼 취급하고 채팅, GitHub, 원고, 로그, 영상 프로젝트 파일에 붙여 넣지
   않습니다.
5. 가능하면 해당 키를 Gemini API 사용으로 제한하고 Google AI Studio의 사용량·결제 설정을 확인합니다.

프로젝트 권한이 없어 생성 버튼이 비활성화되면 프로젝트 관리자에게 키 생성 권한을 요청하거나, 사용자가 관리할 수
있는 새 프로젝트를 선택해야 합니다. 키 발급·쿼터·결제 조건은 Google 계정과 프로젝트 설정에 따라 달라질 수
있습니다.

## 6. 환경변수 등록

### macOS/Linux 현재 터미널에만 등록

키를 복사한 뒤 같은 터미널에서 실행합니다. 아래 자리표시자만 실제 키로 바꿉니다.

```bash
export GEMINI_API_KEY='PASTE_YOUR_KEY_HERE'
```

터미널을 닫으면 사라지는 일회성 등록입니다. 지속 등록이 필요하면 macOS는 `~/.zshrc`, Linux Bash는
`~/.bashrc`에 같은 export 줄을 직접 추가하고 새 터미널에서 다시 확인합니다. 셸 기록과 공유 화면에 키가 남지
않도록 주의하세요.

### Windows PowerShell 현재 세션에만 등록

```powershell
$env:GEMINI_API_KEY = "PASTE_YOUR_KEY_HERE"
```

사용자 계정에 지속 등록하려면 Windows 환경 변수 화면을 사용하는 방법이 가장 안전합니다. PowerShell 명령으로
등록해야 한다면 자리표시자를 실제 키로 바꿔 다음을 실행한 뒤 새 PowerShell을 엽니다.

```powershell
[Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "PASTE_YOUR_KEY_HERE", "User")
```

실제 키를 명령줄에 입력하면 PowerShell 기록이나 화면 공유에 남을 수 있으므로, 기록을 관리할 수 있을 때만
사용하세요. 이 스킬은 `GEMINI_API_KEY`와 `GOOGLE_API_KEY` 중 하나를 읽습니다. 두 변수를 동시에 설정하지
말고 하나만 사용하세요.

## 7. 키를 출력하지 않고 등록 여부 확인

macOS/Linux:

```bash
python scripts/check_environment.py --check-key
```

Windows PowerShell:

```powershell
py scripts\check_environment.py --check-key
```

성공 시 `GEMINI_TTS_KEY=present`만 표시하고 실제 키 문자열은 표시하지 않습니다. 실패 시
`GEMINI_TTS_KEY=not-set`을 표시합니다. `echo $env:GEMINI_API_KEY`, `printenv GEMINI_API_KEY`,
`env`처럼 키 값을 출력하는 명령은 사용하지 마세요.

## 8. Python 패키지 준비와 사용자 승인

시스템 도구가 준비된 뒤 다음 순서로 실행합니다.

```bash
python scripts/prepare_env.py --check
python scripts/prepare_env.py --plan
```

`--plan`은 `.venv` 생성 여부와 `opencv-python`, `numpy`, `av`, `Pillow`, `google-genai` 중 설치할 목록만
보여줍니다. 사용자가 계획을 확인하고 승인한 뒤에만 적용합니다.

```bash
python scripts/prepare_env.py --apply --approved
python scripts/prepare_env.py --check
```

시스템 Python·Git·FFmpeg는 이 명령으로 설치하지 않습니다. 스킬 전용 `.venv`에만 Python 패키지를 설치합니다.

## 9. 설치 실패 시 재시도

### Python·Git·FFmpeg·FFprobe 누락

1. 이 문서의 운영체제별 공식 설치 방법으로 누락 항목을 설치합니다.
2. 터미널을 완전히 닫고 새로 엽니다(PATH 반영).
3. `python scripts/check_environment.py --check`를 다시 실행합니다.
4. `ENV_CHECK=pass`가 될 때까지 영상 제작을 시작하지 않습니다.

### Python 패키지 설치 실패

네트워크, 프록시, 권한, 디스크 공간을 확인합니다. `.venv`나 저장소를 먼저 삭제하지 않습니다. 원인을 해결한
뒤 다음 순서로 같은 계획을 재확인하고 다시 적용합니다.

```bash
python scripts/prepare_env.py --check
python scripts/prepare_env.py --plan
python scripts/prepare_env.py --apply --approved
```

기존 `.venv`가 남아 있으면 설치된 패키지는 유지하고 누락된 패키지만 다시 설치합니다. 같은 실패가 반복되면
오류 메시지와 운영체제·Python 버전을 확인한 뒤 사용자와 다음 조치를 협의합니다.

### Gemini API 키 확인 실패

1. 키 발급 페이지에서 키가 삭제·비활성화되지 않았는지 확인합니다.
2. 현재 TTS를 실행할 바로 그 터미널에 환경변수를 다시 등록합니다.
3. `python scripts/check_environment.py --check-key`로 값이 아닌 등록 상태만 확인합니다.
4. 성공한 뒤 TTS 명령을 다시 실행합니다.

키 값은 오류 보고나 로그에 넣지 않습니다. 키가 노출되었다고 의심되면 Google AI Studio에서 새 키를 발급하고
기존 키를 비활성화·폐기합니다.

### 최초 GitHub 저장소 준비 실패

`references/runtime-bootstrap.md`의 읽기 전용 확인 → 계획 표시 → 사용자 승인 → 적용 순서를 다시 따릅니다.
기존 저장소를 자동 pull, reset, 삭제하거나 덮어쓰지 않습니다.
