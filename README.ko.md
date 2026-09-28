[🇺🇸 English](README.md) | 🇰🇷 한국어

# Product Designer 이력서 작성기

AI 에이전트가 Product Designer 이력서를 Word 또는 편집 가능한 HTML 형식으로 만들어 드립니다. 인터뷰를 통해 정보를 수집하고, 본인의 기여, 디자인 판단, 확인 가능한 근거를 바탕으로 성과를 작성한 뒤, 5가지 레이아웃 중 선택하여 내보냅니다.

## 등록된 스킬

이력서 작성과 리뷰 스킬을 Codex (`.agents/skills`), Claude Code (`.claude/skills`), Cursor (`.cursor/skills`)에 모두 등록했습니다. Copilot은 `.github/skills`의 공통 스킬과 기존 `resume-writer` 에이전트를 사용합니다.

| 기능 | Codex | Claude Code |
| --- | --- | --- |
| 이력서 작성·맞춤 수정 | `$resume-writing` | `/resume-writing` |
| 리뷰 업로드 화면 열기 | `$resume-review` | `/resume-review` |

기존 Claude `/resume-writer` 명령도 유지됩니다. 새 스킬이 보이지 않으면 새 세션을 시작하세요. Cursor/Copilot에서는 스킬을 선택하거나 자연어로 요청할 수 있습니다. 스킬 등록과 AI 연결은 별개이며, 업로드 화면은 Codex, Claude Code, Cursor Agent CLI, GitHub Copilot CLI를 지원합니다. 선택한 CLI의 설치와 로그인이 필요합니다.

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

`python3 .github/skills/resume-writing/scripts/serve_resume.py 이름_Resume.md --layout single-column`을 실행하고 `single-column`을 초기 레이아웃으로 바꾸세요. 미리보기의 Template 메뉴에서 레이아웃을 비교하고 Accent 색상 선택기로 제목과 링크 색상을 바꿀 수 있습니다. Word와 PDF에는 현재 레이아웃, 선택한 강조색, 브라우저 수정 내용이 적용됩니다. 사이드바의 중립 배경색은 유지됩니다. 생성된 미리보기는 리뷰 앱과 동일한 흰색·연회색 화면, 검은색 버튼, 절제된 라임색 강조를 기본으로 사용합니다. Accent 선택은 이력서에 적용되며 미리보기 조작부의 기본 스타일은 유지됩니다. 검토와 다운로드 중에는 서버를 실행 상태로 유지하세요. 브라우저, Word, PDF 렌더링은 조금 다를 수 있습니다. `file://` HTML은 Python 내보내기를 실행할 수 없고, 브라우저 수정 내용은 원본 Markdown에 자동 반영되지 않습니다.

이력서 리뷰는 편집 가능한 내보내기 미리보기와 별도입니다. Markdown 또는 Word 이력서와 타겟 채용공고 URL이나 전체 채용공고 내용을 제공해야 하며, 채용공고가 없으면 에이전트가 리뷰 전에 요청합니다. 주요 요구사항을 추출해 강한 매칭, 부분 매칭, 이력서에서 확인되지 않는 항목을 보여주는 HTML 페이지가 열립니다. 모든 매칭은 이력서의 정확한 근거 문장에 연결되며, 모든 경력 및 프로젝트 bullet은 해당 역할에 맞춰 주도성, 범위, 방법, 결과, 근거, 명확성을 평가받습니다. 같은 이력서에 다른 URL이나 채용공고 내용을 제공하면 매칭 분석을 새로 생성할 수 있습니다. 이는 정성적 리뷰이며 ATS 인증이나 숫자 기반 적합도 점수가 아닙니다.

## 브라우저에서 리뷰 시작하기

```sh
python3 .github/skills/resume-review/scripts/render_review.py
```

파일 인수 없이 실행하면 시작 화면의 로컬 URL이 표시됩니다. `.docx` 또는 `.md` 이력서(최대 5 MB)를 끌어 놓거나 파일 선택으로 추가한 뒤, 채용공고 URL이나 전체 내용을 입력하세요. **Review my resume**를 누르면 타겟 직무에 맞춘 리뷰 스킬을 읽어 분석하고, 근거 문장과 bullet 누락 여부를 검증한 후 리뷰를 자동으로 엽니다. 진행 상태, 오류 후 재시도, 새로고침 후 진행 중인 리뷰 재연결을 지원합니다. **Change job**은 같은 이력서를 새 공고로 다시 분석합니다.

리뷰는 다양한 직무를 지원하며, 포트폴리오, 디자인 방법, 자격증은 해당 직무와 관련될 때만 평가합니다. 별도의 이력서 작성 워크플로는 계속 프로덕트 디자이너에 맞춰져 있습니다.

분석 시에는 스킬의 공통 평가 기준만 읽고 채팅용 파일 저장·화면 열기 지침은 제외합니다. 앱이 이력서 블록에 ID를 부여하고 분석 결과의 ID를 원문으로 복원하여 반복 텍스트를 줄입니다. 모든 경력·프로젝트 불릿과 근거 검증은 유지하며 기존 리뷰도 계속 열 수 있습니다. 업로드 폴더의 `metrics.json`에 처리 시간, 시도 횟수, 입출력 글자 수를 저장합니다. 글자 수는 토큰 사용량이 아니며 처리 시간은 문서, 공고 접근, 모델에 따라 달라집니다.

자동 분석에는 `python-docx`가 설치된 Python과 로그인된 Codex CLI, Claude Code, Cursor Agent CLI 또는 GitHub Copilot CLI가 필요합니다. 선택한 CLI에 설정된 모델과 계정을 사용하며 일반 사용량 제한이 적용됩니다. 이력서 텍스트와 채용공고는 선택한 AI 서비스로 전송됩니다. 업로드와 결과는 Git에서 제외된 `output/reviews/uploads/`에 보관되며 직접 삭제할 때까지 유지됩니다. 서버를 실행 상태로 유지하세요. 한 번에 하나의 리뷰를 분석합니다. 공고 URL을 읽을 수 없다면 전체 내용을 붙여넣으세요. 기존 파일 추출 및 리뷰 렌더링 명령도 계속 사용할 수 있습니다.

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

### 리뷰 스킬 실행과 AI 선택

Codex에서는 `$resume-review`, Claude Code에서는 `/resume-review`로 기존 업로드 화면을 엽니다. 스킬이 해당 도구를 선택해 서버를 시작합니다. 새 스킬이 보이지 않으면 새 세션을 시작하세요. 직접 실행할 때는 `render_review.py --provider codex --open` 또는 `--provider claude --open`을 사용합니다. 도구를 확인할 수 없으면 화면에서 선택합니다. 설치 여부와 로그인 여부는 다르며, 계정 접근은 리뷰 시작 시 확인합니다. **Change job**은 원래 선택한 AI를 유지합니다.

각 리뷰는 별도의 분석 세션이므로 원래 대화나 일회성 모델 설정을 그대로 상속하지 않습니다. Cursor는 `--provider cursor`, Copilot은 `--provider copilot`으로 해당 CLI와 계정을 사용합니다. 에디터 로그인과 CLI 로그인은 다를 수 있습니다. [연결 설정 안내](.github/skills/resume-review/references/provider-setup.md)를 참고하세요.
