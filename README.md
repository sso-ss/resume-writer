🇺🇸 English | [🇰🇷 한국어](README.ko.md)

# Product Designer Resume Writer

An AI agent that creates Product Designer resumes in Word or editable HTML format. It interviews you, writes relevant achievements grounded in ownership, design decisions, and credible evidence, and exports your choice of 5 layouts.

## What It Does

- **Creates resumes from scratch** — answers a few questions, gets a finished `.docx`
- **Rewrites from a paste** — dump your career info and it builds the resume immediately
- **Matches resumes to target jobs** — annotated requirement matches plus content analysis for every experience and project bullet
- **Tailors to job postings** — mirrors keywords from a specific listing
- **5 layout options** — single-column (ATS-safe), two-column left sidebar, classic right sidebar, refined right sidebar, editable editorial HTML

---

## Setup

> **Note:** Python 3 is needed for `.docx` export. The agent will check automatically and guide you through installation if it's missing. macOS users likely already have it.

---

### Option 1: VS Code + GitHub Copilot

Best for most users. Visual interface, no terminal knowledge needed.

#### Install
1. Download [VS Code](https://code.visualstudio.com/)
2. Open VS Code → Extensions (⌘⇧X / Ctrl+Shift+X) → search **"GitHub Copilot"** → Install
3. Sign in with your GitHub account (requires a [Copilot subscription](https://github.com/features/copilot))
4. Open this folder in VS Code: **File → Open Folder…** → select the `Resume` folder

#### Use
1. Open Copilot Chat (click the chat icon or press ⌘⇧I / Ctrl+Shift+I)
2. Select **resume-writer** from the agent dropdown
3. Say something like: *"Help me write a Product Designer resume"*
4. Follow the prompts

---

### Option 2: Cursor

Best for designers already using Cursor. Same visual experience as VS Code.

#### Install
1. Download [Cursor](https://cursor.sh/)
2. Open this folder in Cursor: **File → Open Folder…** → select the `Resume` folder
3. The agent rule loads automatically from `.cursor/rules/resume-writer.mdc`

#### Use
1. Open the AI chat panel (⌘L / Ctrl+L)
2. Switch to **Agent** mode
3. Say something like: *"Help me write a Product Designer resume"*
4. Follow the prompts

> **Note:** In Cursor, the agent reads the rule file automatically when relevant. You can also reference it by typing `@resume-writer` in chat.

---

### Option 3: Claude Code (CLI)

For users comfortable with a terminal.

#### Install
1. Install [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
2. `cd` into the `Resume` folder:
   ```bash
   cd /path/to/Resume
   ```
3. Start a session:
   ```bash
   claude
   ```

#### Use
Type the slash command:
```
/resume-writer
```
Then follow the prompts.

---

## Output

The agent uses a preview-first flow:
1. Creates `YourName_Resume.md` as the source content
2. Opens an editable HTML preview matching your selected layout
3. Generates the matching `.docx` or `.pdf` after you review and export it

## Content Defaults

- **Summary:** Two concise sentences, roughly 30–50 words: positioning plus one achievement relevant to the target role. Optional when it adds no useful information.
- **Experience:** Personal ownership, design judgment, and supported results. Every bullet needs meaningful evidence; not every bullet needs a number.
- **Projects:** Omitted for experienced designers when they repeat Experience. Include projects that demonstrate otherwise missing relevant abilities; link case studies beside related work where useful.
- **Skills:** Compact Design, Research, and Collaboration & Leadership categories, generally 3–4 relevant items each, plus a short Tools line. Keep soft skills visible and demonstrate them in Experience.
- **AI:** Include supported workflow/product-design capabilities and validation when relevant; add an AI skills line or summary mention only when it helps the application.
- **Level and length:** Assess seniority by responsibility and scope. Aim for one readable page; allow two when relevant experience warrants it.
- **Final review:** Check recruiter concerns (fit, chronology, portfolio access) and hiring-manager concerns (ownership, judgment, collaboration, credible impact).

[`Jennifer_Lauren_Resume.md`](Jennifer_Lauren_Resume.md) is a fictional content example, including its employers, education, achievements, and numbers. Its `example.com` links are placeholders, not a live portfolio. It demonstrates the revised writing defaults; older Word examples may reflect previous content. Replace demo claims and links with verified personal information before applying.

## Layout Options

| Layout | Command | Best For |
|---|---|---|
| **Single Column** (default) | `single-column` | ATS systems, job boards, recruiter portals |
| **Two-Column Left** | `two-column-left` | Portfolio-style feel, direct applications |
| **Two-Column Right** | `two-column-right` | F-pattern reading, networking, direct outreach |
| **Two-Column Right Refined** | `two-column-right-refined` | Full-width summary and balanced sidebar, direct outreach |
| **Editorial HTML** | `editorial-html` | Editable browser layout, print to PDF for direct sharing |

> **ATS Warning:** Two-column layouts may reduce ATS parsing accuracy. Use `single-column` when applying through job boards or company career pages.

Run `python3 .github/skills/resume-writing/scripts/serve_resume.py YourName_Resume.md --layout single-column`, replacing `single-column` with your initial layout. Use the Template menu to compare layouts and the Accent picker to change heading/link color; Word and PDF exports include the selected layout, accent, and browser edits. The neutral sidebar background stays fixed. Keep the server running while reviewing and downloading. Rendering can differ slightly between browser, Word, and PDF. Standalone `file://` HTML cannot invoke Python, and browser edits do not change the original Markdown.

Resume review is separate from the editable export preview. Upload a Markdown or Word resume with a target job URL or the full pasted job description; if the posting is missing, the agent asks for it before reviewing. The agent extracts the role's main requirements and opens an HTML page showing strong matches, partial matches, and requirements not demonstrated in the resume. Every match links to exact resume evidence, and every Experience and Projects bullet receives role-specific feedback on ownership, scope, method, outcome, evidence, and clarity. Provide another URL or pasted description at any time to regenerate the matching analysis for the same resume. This is a qualitative review, not an ATS certification or numeric match score.

### PDF Download Setup
Install these dependencies in the same Python environment as the preview server:
```sh
python3 -m pip install -r .github/skills/resume-writing/requirements-pdf.txt
python3 -m playwright install chromium
```
The current **Save as PDF** button downloads a text-based PDF through local Chromium instead of opening a print dialog. It includes browser edits. Check the downloaded file's page count; selectable text does not guarantee ATS compatibility.

## Example Prompts

**Start from scratch:**
> Help me write a Product Designer resume

**Paste your info:**
> Here's my experience, please build a resume:
> - Senior Product Designer at Example Music Co., 2021-present
> - Led redesign of playlist creation flow, increased saves by 25%
> - Built design system with 80+ components adopted by 4 teams
> ...

**Tailor to a job posting:**
> Tailor my resume to this job posting: https://example.com/jobs/senior-product-designer

**Review an existing resume:**
> Review my uploaded resume for this job and show me annotated feedback: https://example.com/jobs/senior-product-designer

**Choose a layout:**
> Generate my resume in two-column-left layout

**New grad:**
> I'm graduating in May with a BFA in Interaction Design. Help me write a resume

## Tips for Best Results

- Have your **portfolio URL** ready — the agent asks for it first and treats it as critical
- Prepare **2–3 relevant achievements** for each role: what you owned, the decision or constraint, what changed, and how you evaluated it. Include verified metrics when available; concrete qualitative evidence is welcome.
- Describe actual **AI use and validation** when relevant, and give examples of collaboration or leadership. Do not add tools or skills just because a posting mentions them.
- If you have a **job posting** you're targeting, paste the URL — the agent will tailor your resume to match its keywords
- Choose `single-column` unless you're sending the resume directly to someone (not through a job board)

## Project Structure

```
Resume/
├── README.md                            ← you are here
├── README.ko.md                         ← 한국어 가이드
├── .claude/
│   └── commands/
│       └── resume-writer.md             ← Claude Code slash command
├── .cursor/
│   └── rules/
│       └── resume-writer.mdc            ← Cursor agent rule
├── .github/
│   ├── agents/
│   │   └── resume-writer.agent.md       ← VS Code Copilot agent
│   └── skills/
│       ├── resume-review/                ← annotated HTML review workflow
│       └── resume-writing/
│       ├── SKILL.md                     ← writing & evidence guidelines
│       ├── references/
│       │   └── recruiter-guidelines.md  ← section-by-section rules
│       └── scripts/
│           ├── to_docx.py               ← single-column converter
│           ├── to_docx_two_column.py    ← two-column-left converter
│           ├── to_docx_right_sidebar.py         ← two-column-right converter
│           ├── to_docx_right_sidebar_refined.py ← refined right-sidebar converter
│           └── to_html_editorial.py             ← editorial HTML converter
└── {Name}_Resume.md                     ← generated resume (Markdown)
└── {Name}_ProductDesigner_Resume.docx   ← generated resume (Word)
```
