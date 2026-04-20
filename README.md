🇺🇸 English | [🇰🇷 한국어](README.ko.md)

# Product Designer Resume Writer

An AI agent that creates one-page Product Designer resumes in `.docx` format. It interviews you, writes metric-driven bullets using the XYZ formula, and exports a polished Word document in your choice of 3 layouts.

## What It Does

- **Creates resumes from scratch** — answers a few questions, gets a finished `.docx`
- **Rewrites from a paste** — dump your career info and it builds the resume immediately
- **Reviews existing resumes** — section-by-section feedback with suggested rewrites
- **Tailors to job postings** — mirrors keywords from a specific listing
- **3 layout options** — single-column (ATS-safe), two-column left sidebar, two-column right sidebar

---

## Setup

### Prerequisites (all platforms)

1. **Python 3** — download from [python.org](https://python.org) (check **"Add Python to PATH"** during install)
   - macOS users: you may already have it (check with `python3 --version` in Terminal)
   - The agent will automatically install any needed Python packages — no terminal commands required

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

The agent creates two files in this folder:
- `YourName_Resume.md` — the resume content in Markdown
- `YourName_ProductDesigner_Resume.docx` — the final Word document

## Layout Options

| Layout | Command | Best For |
|---|---|---|
| **Single Column** (default) | `single-column` | ATS systems, job boards, recruiter portals |
| **Two-Column Left** | `two-column-left` | Portfolio-style feel, direct applications |
| **Two-Column Right** | `two-column-right` | F-pattern reading, networking, direct outreach |

> **ATS Warning:** Two-column layouts may reduce ATS parsing accuracy. Use `single-column` when applying through job boards or company career pages.

## Example Prompts

**Start from scratch:**
> Help me write a Product Designer resume

**Paste your info:**
> Here's my experience, please build a resume:
> - Senior Product Designer at Spotify, 2021-present
> - Led redesign of playlist creation flow, increased saves by 25%
> - Built design system with 80+ components adopted by 4 teams
> ...

**Tailor to a job posting:**
> Tailor my resume to this job posting: https://example.com/jobs/senior-product-designer

**Review an existing resume:**
> Review my resume and tell me what to fix: [paste resume text]

**Choose a layout:**
> Generate my resume in two-column-left layout

**New grad:**
> I'm graduating in May with a BFA in Interaction Design. Help me write a resume

## Tips for Best Results

- Have your **portfolio URL** ready — the agent asks for it first and treats it as critical
- Prepare **2-3 achievements with numbers** for each role (e.g., "increased conversion by 15%", "conducted 20 user interviews")
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
│   └── skills/resume-writing/
│       ├── SKILL.md                     ← procedures & XYZ formula
│       ├── references/
│       │   └── recruiter-guidelines.md  ← section-by-section rules
│       └── scripts/
│           ├── to_docx.py               ← single-column converter
│           ├── to_docx_two_column.py    ← two-column-left converter
│           └── to_docx_right_sidebar.py ← two-column-right converter
└── {Name}_Resume.md                     ← generated resume (Markdown)
└── {Name}_ProductDesigner_Resume.docx   ← generated resume (Word)
```
