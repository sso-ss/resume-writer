[🇺🇸 English](README.md) | 🇰🇷 한국어

# Product Designer 이력서 작성기

AI 에이전트가 Product Designer 이력서를 Word 또는 편집 가능한 HTML 형식으로 만들어 드립니다. 인터뷰를 통해 정보를 수집하고, 본인의 기여, 디자인 판단, 확인 가능한 근거를 바탕으로 성과를 작성한 뒤, 5가지 레이아웃 중 선택하여 내보냅니다.

## 주요 기능

- **처음부터 이력서 작성** — 몇 가지 질문에 답하면 완성된 `.docx` 파일 제공
- **기존 정보 붙여넣기** — 경력 정보를 붙여넣으면 바로 이력서 생성
- **타겟 채용공고와 이력서 매칭** — 요구사항별 매칭과 모든 경력·프로젝트 bullet 분석을 HTML 주석으로 제공
- **채용공고 맞춤화** — 특정 채용공고의 키워드를 반영
- **5가지 레이아웃** — 단일 컬럼(ATS 호환), 2단 좌측 사이드바, 2단 우측 사이드바, 개선된 2단 우측 사이드바, 편집 가능한 HTML

---

## 설치 방법

> **참고:** `.docx` 내보내기에 Python 3이 필요합니다. 에이전트가 자동으로 확인하고, 설치가 필요한 경우 안내해 드립니다. macOS 사용자는 이미 설치되어 있을 수 있습니다.

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

에이전트는 미리보기 우선 순서로 진행합니다:
1. 원본 콘텐츠인 `이름_Resume.md` 생성
2. 선택한 레이아웃과 일치하는 편집 가능한 HTML 미리보기 열기
3. 검토 후 같은 레이아웃의 `.docx` 또는 `.pdf` 내보내기

## 콘텐츠 작성 기본 원칙

- **요약:** 영어 기준 약 30–50단어의 간결한 두 문장으로 전문 분야와 지원 직무에 관련된 성과 하나를 보여줍니다. 새로운 정보를 더하지 않으면 생략할 수 있습니다.
- **경력:** 본인의 책임, 디자인 판단, 근거 있는 결과를 강조합니다. 모든 bullet에 숫자가 필요하지는 않습니다.
- **프로젝트:** 경력과 중복되는 별도 프로젝트 섹션은 기본적으로 생략합니다. 경력에서 확인되지 않는 관련 역량을 보여줄 때 포함하고, 사례 링크는 해당 경력 옆에 배치할 수 있습니다.
- **역량:** Design, Research, Collaboration & Leadership을 중심으로 각각 관련 항목 3–4개 정도와 짧은 Tools 줄을 사용합니다. 소프트 스킬을 유지하고 경력에서 근거를 보여줍니다.
- **AI:** 실제 활용 또는 AI 제품 설계와 검증 경험이 지원 직무에 도움이 될 때 포함합니다. AI 역량 줄이나 요약 문구는 선택 사항입니다.
- **직급과 분량:** 연차만으로 직급을 정하지 않고 책임과 영향 범위를 봅니다. 읽기 쉬운 한 페이지를 목표로 하되 관련 경력이 충분하면 두 페이지를 허용합니다.
- **최종 검토:** 리크루터 관점의 직무 적합성·경력 흐름·포트폴리오 접근성과 채용 매니저 관점의 주도성·판단·협업·성과의 신뢰성을 확인합니다.

[`Jennifer_Lauren_Resume.md`](Jennifer_Lauren_Resume.md)는 회사, 학력, 성과, 수치를 포함한 가상 예시입니다. `example.com` 링크는 실제 포트폴리오가 아닌 예시 주소입니다. 최신 작성 원칙을 보여주는 Markdown이며 기존 Word 예시는 이전 내용을 포함할 수 있습니다. 실제 지원 시 본인의 확인된 정보와 링크로 교체하세요.

## 레이아웃 옵션

| 레이아웃 | 명령어 | 적합한 용도 |
|---|---|---|
| **단일 컬럼** (기본값) | `single-column` | ATS 시스템, 채용 사이트, 리크루터 포탈 |
| **2단 좌측** | `two-column-left` | 포트폴리오 스타일, 직접 지원 |
| **2단 우측** | `two-column-right` | F패턴 읽기, 네트워킹, 직접 전달 |
| **개선된 2단 우측** | `two-column-right-refined` | 전체 너비 요약 및 균형 잡힌 사이드바, 직접 전달 |
| **에디토리얼 HTML** | `editorial-html` | 브라우저에서 편집 후 PDF로 인쇄하여 직접 전달 |

> **ATS 주의사항:** 2단 레이아웃은 ATS 파싱 정확도가 떨어질 수 있습니다. 채용 사이트나 회사 채용 페이지를 통해 지원할 때는 `single-column`을 사용하세요.

`python3 .github/skills/resume-writing/scripts/serve_resume.py 이름_Resume.md --layout single-column`을 실행하고 `single-column`을 초기 레이아웃으로 바꾸세요. 미리보기의 Template 메뉴에서 레이아웃을 비교하고 Accent 색상 선택기로 제목과 링크 색상을 바꿀 수 있습니다. Word와 PDF에는 현재 레이아웃, 선택한 강조색, 브라우저 수정 내용이 적용됩니다. 사이드바의 중립 배경색은 유지됩니다. 검토와 다운로드 중에는 서버를 실행 상태로 유지하세요. 브라우저, Word, PDF 렌더링은 조금 다를 수 있습니다. `file://` HTML은 Python 내보내기를 실행할 수 없고, 브라우저 수정 내용은 원본 Markdown에 자동 반영되지 않습니다.

이력서 리뷰는 편집 가능한 내보내기 미리보기와 별도입니다. Markdown 또는 Word 이력서와 타겟 채용공고 URL이나 전체 채용공고 내용을 제공해야 하며, 채용공고가 없으면 에이전트가 리뷰 전에 요청합니다. 주요 요구사항을 추출해 강한 매칭, 부분 매칭, 이력서에서 확인되지 않는 항목을 보여주는 HTML 페이지가 열립니다. 모든 매칭은 이력서의 정확한 근거 문장에 연결되며, 모든 경력 및 프로젝트 bullet은 해당 역할에 맞춰 주도성, 범위, 방법, 결과, 근거, 명확성을 평가받습니다. 같은 이력서에 다른 URL이나 채용공고 내용을 제공하면 매칭 분석을 새로 생성할 수 있습니다. 이는 정성적 리뷰이며 ATS 인증이나 숫자 기반 적합도 점수가 아닙니다.

## 프롬프트 예시

**처음부터 작성:**
> Help me write a Product Designer resume

**정보 붙여넣기:**
> Here's my experience, please build a resume:
> - Senior Product Designer at Example Music Co., 2021-present
> - Led redesign of playlist creation flow, increased saves by 25%
> - Built design system with 80+ components adopted by 4 teams
> ...

**채용공고에 맞춤화:**
> Tailor my resume to this job posting: https://example.com/jobs/senior-product-designer

**기존 이력서 리뷰:**
> Review my uploaded resume for this job and show me annotated feedback: https://example.com/jobs/senior-product-designer

**레이아웃 선택:**
> Generate my resume in two-column-left layout

**신입/졸업예정:**
> I'm graduating in May with a BFA in Interaction Design. Help me write a resume

## 더 나은 결과를 위한 팁

- **포트폴리오 URL**을 준비하세요 — 에이전트가 가장 먼저 물어보며 필수로 취급합니다
- 각 직무별로 **관련성 높은 성과 2–3개**를 준비하세요. 본인의 책임, 주요 결정이나 제약, 변화, 평가 방법을 설명하고 확인 가능한 수치가 있다면 포함하세요. 구체적인 정성적 근거도 사용할 수 있습니다.
- 관련성이 있다면 실제 **AI 활용과 검증 방법**, 협업 및 리더십 사례를 준비하세요. 공고에 나온다는 이유만으로 사용하지 않은 도구나 역량을 추가하지 않습니다.
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
│   └── skills/
│       ├── resume-review/                ← 주석이 포함된 HTML 리뷰 워크플로
│       └── resume-writing/
│       ├── SKILL.md                     ← 작성 절차 및 근거 중심 가이드
│       ├── references/
│       │   └── recruiter-guidelines.md  ← 항목별 작성 규칙
│       └── scripts/
│           ├── to_docx.py               ← 단일 컬럼 변환기
│           ├── to_docx_two_column.py    ← 2단 좌측 변환기
│           ├── to_docx_right_sidebar.py         ← 2단 우측 변환기
│           ├── to_docx_right_sidebar_refined.py ← 개선된 2단 우측 변환기
│           └── to_html_editorial.py             ← 에디토리얼 HTML 변환기
└── {이름}_Resume.md                     ← 생성된 이력서 (Markdown)
└── {이름}_ProductDesigner_Resume.docx   ← 생성된 이력서 (Word)
```
