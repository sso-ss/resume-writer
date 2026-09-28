🇺🇸 English | [🇰🇷 한국어](README.ko.md)

# Product Designer Resume Writer

An AI agent that creates Product Designer resumes in Word or editable HTML format. It interviews you, writes relevant achievements grounded in ownership, design decisions, and credible evidence, and exports your choice of 5 layouts.

## Available Skills

Both skills are registered in the repository for Codex (`.agents/skills`), Claude Code (`.claude/skills`), and Cursor (`.cursor/skills`). Copilot uses the canonical `.github/skills` directories and the existing `resume-writer` agent.

| Task | Codex | Claude Code |
| --- | --- | --- |
| Build or tailor a resume | `$resume-writing` | `/resume-writing` |
| Open Resume Review | `$resume-review` | `/resume-review` |

Claude's existing `/resume-writer` command remains available. In Cursor or Copilot, select the available skill or ask to build/review a resume. Restart the host session if newly registered skills are not visible. The upload screen supports Codex CLI, Claude Code, Cursor Agent CLI, and GitHub Copilot CLI. Install and sign in to the selected CLI; being signed in to an editor alone may not sign in its CLI.

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

Run `python3 .github/skills/resume-writing/scripts/serve_resume.py YourName_Resume.md --layout single-column`, replacing `single-column` with your initial layout. Use the Template menu to compare layouts and the Accent picker to change heading/link color; Word and PDF exports include the selected layout, accent, and browser edits. The neutral sidebar background stays fixed. Generated previews share the review app’s white and light-gray interface, black action buttons, and restrained lime accents. The Accent picker changes the resume; preview controls keep their default style. Keep the server running while reviewing and downloading. Rendering can differ slightly between browser, Word, and PDF. Standalone `file://` HTML cannot invoke Python, and browser edits do not change the original Markdown.

Resume review is separate from the editable export preview. Upload a Markdown or Word resume with a target job URL or the full pasted job description; if the posting is missing, the agent asks for it before reviewing. The agent extracts the role's main requirements and opens an HTML page showing strong matches, partial matches, and requirements not demonstrated in the resume. Every match links to exact resume evidence, and every Experience and Projects bullet receives role-specific feedback on ownership, scope, method, outcome, evidence, and clarity. Provide another URL or pasted description at any time to regenerate the matching analysis for the same resume. This is a qualitative review, not an ATS certification or numeric match score.

### Start a review in the browser

Run the review tool without a resume argument to open its starting screen:

```sh
python3 .github/skills/resume-review/scripts/render_review.py
```

Open the printed local URL. Drag in a `.docx` or `.md` resume (up to 5 MB), or choose it from your files, then add a job posting URL or paste the full description. **Review my resume** starts the analysis and opens the annotated review automatically. The page shows progress, supports retrying after errors, and reconnects to a running review after a reload. **Change job** reruns the analysis for the same resume; **Review another resume** returns to the starting screen.

Automatic analysis requires Python with `python-docx` and an installed, signed-in [Codex CLI](https://developers.openai.com/codex/cli/) , [Claude Code](https://code.claude.com/docs/en/overview), [Cursor Agent CLI](https://cursor.com/docs/cli/overview), or [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/cli-getting-started). The selected CLI uses its own account and configured model; normal usage limits apply. It runs a separate analysis session, so it does not inherit the launching conversation or necessarily its model override. Each request loads the skill’s shared review criteria, adapted to the target job, without chat-only workflow instructions. Reviews support different professions; portfolios, design methods, and credentials are assessed only when relevant. The separate resume-writing workflow remains tailored to product designers. Codex runs read-only; Claude is restricted to web-reading tools with no shell/edit tools or configured MCP servers. Cursor uses Ask mode with shell/write/MCP operations denied; Copilot exposes only web fetching. All return structured findings; the app checks quotes and bullet coverage before displaying the result. If a job URL cannot be read, paste the full description.

The app assigns resume block IDs before analysis and restores exact text from those IDs afterward, reducing repeated text in the response. Full bullet coverage and evidence validation remain required; existing saved reviews remain compatible. Each upload folder includes `metrics.json` with elapsed time, attempt count, and input/output character counts for comparison. These are character counts, not token usage; timing varies with the resume, posting access, and configured model.

Resume text and job details are sent to the selected AI provider for analysis. Uploads and results stay in `output/reviews/uploads/` until you remove them; this folder is excluded from Git. Keep the local server running while reviewing. One analysis runs at a time. The existing extraction and pre-generated review commands still work.

### Skill shortcuts and AI selection

- **Codex:** `$resume-review` uses the repository skill registered in `.agents/skills/resume-review` and opens the upload screen with Codex selected.
- **Claude Code:** `/resume-review` uses `.claude/skills/resume-review` and opens the same screen with Claude selected.
- **Cursor:** its resume-review skill launches with `--provider cursor`, using Cursor Agent CLI and the user’s Cursor account.
- **GitHub Copilot:** the resume-writer agent/shared skill launches with `--provider copilot`, using GitHub Copilot CLI and the user’s GitHub account.
- **Unknown terminals:** choose the desired installed AI tool on the screen.

Start a new host session if the new shortcut is not visible. For manual launch, use `--provider codex --open` , `--provider claude --open`, `--provider cursor --open`, or `--provider copilot --open`. Without an explicit provider, an unambiguous terminal marker selects it; otherwise the screen asks. The screen distinguishes a missing executable from an installed tool; sign-in is checked when review begins. **Change job** retains the original provider. See [.github/skills/resume-review/references/provider-setup.md](.github/skills/resume-review/references/provider-setup.md) for setup and adapter details. Do not share localhost links with other users; they launch their own local server.

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
