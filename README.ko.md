[🇺🇸 English](README.md) | 🇰🇷 한국어

# Product Designer 이력서 작성기

AI 에이전트가 1페이지 Product Designer 이력서를 `.docx` 형식으로 만들어 드립니다. 인터뷰를 통해 정보를 수집하고, XYZ 공식으로 성과 중심 문장을 작성한 뒤, 3가지 레이아웃 중 선택하여 Word 문서로 내보냅니다.

## 주요 기능

- **처음부터 이력서 작성** — 몇 가지 질문에 답하면 완성된 `.docx` 파일 제공
- **기존 정보 붙여넣기** — 경력 정보를 붙여넣으면 바로 이력서 생성
- **기존 이력서 리뷰** — 항목별 피드백과 수정안 제시
- **채용공고 맞춤화** — 특정 채용공고의 키워드를 반영
- **3가지 레이아웃** — 단일 컬럼(ATS 호환), 2단 좌측 사이드바, 2단 우측 사이드바

---

## 설치 방법

### 사전 준비 (모든 플랫폼 공통)

1. **Python 3** — [python.org](https://python.org) 에서 다운로드 (설치 시 **"Add Python to PATH"** 체크)
   - macOS 사용자: 이미 설치되어 있을 수 있습니다 (터미널에서 `python3 --version`으로 확인)
   - 필요한 Python 패키지는 에이전트가 자동으로 설치합니다 — 터미널 명령어 입력 불필요

---

### 방법 1: VS Code + GitHub Copilot

대부분의 사용자에게 권장. 시각적 인터페이스, 터미널 지식 불필요.

#### 설치
1. [VS Code](https://code.visualstudio.com/) 다운로드
2. VS Code 열기 → 확장(⌘⇧X / Ctrl+Shift+X) → **"GitHub Copilot"** 검색 → 설치
3. GitHub 계정으로 로그인 ([Copilot 구독](https://github.com/features/copilot) 필요)
4. VS Code에서 이 폴더 열기: **파일 → 폴더 열기…** → `Resume` 폴더 선택

#### 사용법
1. Copilot Chat 열기 (채팅 아이콘 클릭 또는 ⌘⇧I / Ctrl+Shift+I)
2. 에이전트 드롭다운에서 **resume-writer** 선택
3. 입력 예시: *"Help me write a Product Designer resume"*
4. 안내에 따라 진행

---

### 방법 2: Cursor

이미 Cursor를 사용 중인 디자이너에게 추천. VS Code와 비슷한 인터페이스.

#### 설치
1. [Cursor](https://cursor.sh/) 다운로드
2. Cursor에서 이 폴더 열기: **File → Open Folder…** → `Resume` 폴더 선택
3. 에이전트 규칙이 `.cursor/rules/resume-writer.mdc`에서 자동으로 로드됩니다

#### 사용법
1. AI 채팅 패널 열기 (⌘L / Ctrl+L)
2. **Agent** 모드로 전환
3. 입력 예시: *"Help me write a Product Designer resume"*
4. 안내에 따라 진행

> **참고:** Cursor에서는 관련 대화 시 규칙 파일이 자동으로 적용됩니다. 채팅에서 `@resume-writer`를 입력하여 직접 참조할 수도 있습니다.

---

### 방법 3: Claude Code (CLI)

터미널에 익숙한 사용자용.

#### 설치
1. [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 설치
2. 터미널에서 `Resume` 폴더로 이동:
   ```bash
   cd /path/to/Resume
   ```
3. 세션 시작:
   ```bash
   claude
   ```

#### 사용법
슬래시 명령어 입력:
```
/resume-writer
```
이후 안내에 따라 진행하세요.

---

## 결과물

에이전트가 이 폴더에 두 개의 파일을 생성합니다:
- `이름_Resume.md` — Markdown 형식의 이력서 내용
- `이름_ProductDesigner_Resume.docx` — 최종 Word 문서

## 레이아웃 옵션

| 레이아웃 | 명령어 | 적합한 용도 |
|---|---|---|
| **단일 컬럼** (기본값) | `single-column` | ATS 시스템, 채용 사이트, 리크루터 포탈 |
| **2단 좌측** | `two-column-left` | 포트폴리오 스타일, 직접 지원 |
| **2단 우측** | `two-column-right` | F패턴 읽기, 네트워킹, 직접 전달 |

> **ATS 주의사항:** 2단 레이아웃은 ATS 파싱 정확도가 떨어질 수 있습니다. 채용 사이트나 회사 채용 페이지를 통해 지원할 때는 `single-column`을 사용하세요.

## 프롬프트 예시

**처음부터 작성:**
> Help me write a Product Designer resume

**정보 붙여넣기:**
> Here's my experience, please build a resume:
> - Senior Product Designer at Spotify, 2021-present
> - Led redesign of playlist creation flow, increased saves by 25%
> - Built design system with 80+ components adopted by 4 teams
> ...

**채용공고에 맞춤화:**
> Tailor my resume to this job posting: https://example.com/jobs/senior-product-designer

**기존 이력서 리뷰:**
> Review my resume and tell me what to fix: [이력서 텍스트 붙여넣기]

**레이아웃 선택:**
> Generate my resume in two-column-left layout

**신입/졸업예정:**
> I'm graduating in May with a BFA in Interaction Design. Help me write a resume

## 더 나은 결과를 위한 팁

- **포트폴리오 URL**을 준비하세요 — 에이전트가 가장 먼저 물어보며 필수로 취급합니다
- 각 직무별로 **숫자가 포함된 성과 2-3개**를 준비하세요 (예: "전환율 15% 향상", "사용자 인터뷰 20회 진행")
- 타겟하는 **채용공고**가 있다면 URL을 붙여넣으세요 — 에이전트가 키워드에 맞춰 이력서를 조정합니다
- 채용 사이트를 통하지 않고 직접 전달하는 경우가 아니라면 `single-column`을 선택하세요

## 프로젝트 구조

```
Resume/
├── README.md                            ← English guide
├── README.ko.md                         ← 한국어 가이드 (현재 파일)
├── .claude/
│   └── commands/
│       └── resume-writer.md             ← Claude Code 슬래시 명령어
├── .cursor/
│   └── rules/
│       └── resume-writer.mdc            ← Cursor 에이전트 규칙
├── .github/
│   ├── agents/
│   │   └── resume-writer.agent.md       ← VS Code Copilot 에이전트
│   └── skills/resume-writing/
│       ├── SKILL.md                     ← 절차 및 XYZ 공식
│       ├── references/
│       │   └── recruiter-guidelines.md  ← 항목별 작성 규칙
│       └── scripts/
│           ├── to_docx.py               ← 단일 컬럼 변환기
│           ├── to_docx_two_column.py    ← 2단 좌측 변환기
│           └── to_docx_right_sidebar.py ← 2단 우측 변환기
└── {이름}_Resume.md                     ← 생성된 이력서 (Markdown)
└── {이름}_ProductDesigner_Resume.docx   ← 생성된 이력서 (Word)
```
