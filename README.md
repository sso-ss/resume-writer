🇺🇸 English | [🇰🇷 한국어](README.ko.md)

# Resume Writer & Review

Create and tailor Product Designer resumes, or review an existing resume against a target job. The writing workflow produces an editable HTML preview with Word and PDF exports in five layouts. Resume Review supports different professions and provides feedback linked to exact resume evidence.

## Quick Start (npm)

Install [Node.js 20 or newer](https://nodejs.org/), then run:

```sh
npx @sso_ss/resume-writer
```

This downloads the app, sets up a private Python environment and its dependencies, and opens Resume Review in your browser. No repository clone, manual Python install, or environment activation is needed. Choose an installed AI provider, upload a `.md` or `.docx` resume, and add the target job URL or full description.

The review app uses your existing AI account. Install and sign in to one supported CLI—Codex, Claude Code, Cursor Agent, or GitHub Copilot—using the [provider setup guide](https://github.com/sso-ss/resume-writer/blob/main/.github/skills/resume-review/references/provider-setup.md). An editor login alone may not sign in its CLI.

```sh
# Review with a specific AI provider
npx @sso_ss/resume-writer review --provider claude

# Edit your Markdown resume and download Word or PDF
npx @sso_ss/resume-writer preview "YourName_Resume.md"

# Prepare everything, including PDF export, without starting a server
npx @sso_ss/resume-writer setup --pdf
```

Preview automatically installs Chromium and the PDF dependencies on first use. Downloads are reused on later launches. First setup needs internet access and may take a few minutes. On Linux, Chromium may additionally require system libraries; its error message lists missing packages. Keep the terminal running while using the app and press Ctrl+C to stop it. Add `--no-open` to print the local URL without opening a browser, or `--help` to see options.

For a permanent command:

```sh
npm install -g @sso_ss/resume-writer
resume-writer
```

The launcher stores its runtime in `~/Library/Caches/resume-writer` on macOS, `$XDG_CACHE_HOME/resume-writer` (or `~/.cache/resume-writer`) on Linux, and `%LOCALAPPDATA%\resume-writer` on Windows. Set `RESUME_WRITER_HOME` to change that location. It downloads [uv from Astral](https://docs.astral.sh/uv/reference/installer/) to manage Python without changing your shell configuration. Uploads and reviews are saved in `output/reviews/uploads/` under the directory where you run the command; they are separate from the runtime cache.

### Run from this repository

Open this repository in your AI tool to use the writing and review skills below. To try the npm launcher before installing it:

```sh
node bin/resume-writer.mjs
node bin/resume-writer.mjs preview Jennifer_Lauren_Resume.md
```

For direct Python use, prepare an environment once:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, create the environment with `py -m venv .venv` and activate it with `.venv\Scripts\Activate.ps1` in PowerShell. Use `python` instead of `python3` below if needed. Keep the environment active when launching Python scripts directly.

## Available Skills

Both skills are registered in the repository for Codex (`.agents/skills`), Claude Code (`.claude/skills`), and Cursor (`.cursor/skills`). Copilot uses the canonical `.github/skills` directories and the existing `resume-writer` agent.

| Task | Codex | Claude Code |
| --- | --- | --- |
| Build or tailor a resume | `$resume-writing` | `/resume-writing` |
| Open Resume Review | `$resume-review` | `/resume-review` |

Claude's existing `/resume-writer` command remains available. In Cursor or Copilot, select the available skill or ask to build/review a resume. Restart the host session if newly registered skills are not visible. The upload screen supports Codex CLI, Claude Code, Cursor Agent CLI, and GitHub Copilot CLI. Install and sign in to the selected CLI; being signed in to an editor alone may not sign in its CLI.

## What It Does

- **Creates resumes from scratch** — answer a few questions, review the preview, and export Word or PDF
- **Rewrites from a paste** — dump your career info and it builds the resume immediately
- **Matches resumes to target jobs** — annotated requirement matches plus content analysis for every experience and project bullet
- **Tailors to job postings** — emphasizes relevant experience and supported keywords from a specific listing
- **5 layout options** — single-column (ATS-safe), two-column left sidebar, classic right sidebar, refined right sidebar, editable editorial HTML

---

## Setup

The [npm quick start](#quick-start-npm) handles the app’s Python and export dependencies automatically. The options below describe using repository skills in an AI editor or CLI. Direct Python commands require the environment described above. Browser review also requires a supported AI CLI installed and signed in.

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
| **Editorial HTML** | `editorial-html` | Editable browser layout with Word and PDF export for direct sharing |

> **ATS Warning:** Two-column layouts may reduce ATS parsing accuracy. Use `single-column` when applying through job boards or company career pages.

The writing workflow recommends `single-column`; the preview script defaults to `editorial-html` if `--layout` is omitted.

Run `python3 .github/skills/resume-writing/scripts/serve_resume.py YourName_Resume.md --layout single-column`, replacing `single-column` with your initial layout. Use the Template menu to compare layouts and the Accent picker to change heading/link color; Word and PDF exports include the selected layout, accent, and browser edits. The neutral sidebar background stays fixed. Generated previews share the review app’s white and light-gray interface, black action buttons, and restrained lime accents. The Accent picker changes the resume; preview controls keep their default style. Keep the server running while reviewing and downloading. Rendering can differ slightly between browser, Word, and PDF. Standalone `file://` HTML cannot invoke Python, and browser edits do not change the original Markdown.

Resume review is separate from the editable export preview. Upload a Markdown or Word resume with a target job URL or the full pasted job description; if the posting is missing, the agent asks for it before reviewing. The agent extracts the role's main requirements and opens an HTML page showing strong matches, partial matches, and requirements not demonstrated in the resume. Every match links to exact resume evidence, and every Experience and Projects bullet receives role-specific feedback on ownership, scope, method, outcome, evidence, and clarity. Provide another URL or pasted description at any time to regenerate the matching analysis for the same resume. This is a qualitative review, not an ATS certification or numeric match score.

## Resume Review

### Start a review in the browser

Run the review tool without a resume argument to open its starting screen:

```sh
python3 .github/skills/resume-review/scripts/render_review.py
```

Open the printed local URL. Drag in a `.docx` or `.md` resume (up to 5 MB), or choose it from your files, then add a job posting URL or paste the full description. **Review my resume** starts the analysis and opens the annotated review automatically. The page shows progress, supports retrying after errors, and reconnects to a running review after a reload. **Change job** reruns the analysis for the same resume; **Review another resume** returns to the starting screen.

Automatic analysis requires Python with `python-docx` and an installed, signed-in [Codex CLI](https://developers.openai.com/codex/cli/), [Claude Code](https://code.claude.com/docs/en/overview), [Cursor Agent CLI](https://cursor.com/docs/cli/overview), or [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/cli-getting-started). The selected CLI uses its own account and configured model; normal usage limits apply. It runs a separate analysis session, so it does not inherit the launching conversation or necessarily its model override. Each request loads the skill’s shared review criteria, adapted to the target job, without chat-only workflow instructions. Reviews support different professions; portfolios, design methods, and credentials are assessed only when relevant. The separate resume-writing workflow remains tailored to product designers. Codex runs read-only; Claude is restricted to web-reading tools with no shell/edit tools or configured MCP servers. Cursor uses Ask mode with shell/write/MCP operations denied; Copilot exposes only web fetching. All return structured findings; the app checks quotes and bullet coverage before displaying the result. If a job URL cannot be read, paste the full description.

The app assigns resume block IDs before analysis and restores exact text from those IDs afterward, reducing repeated text in the response. Full bullet coverage and evidence validation remain required; existing saved reviews remain compatible. Each upload folder includes `metrics.json` with elapsed time, attempt count, and input/output character counts for comparison. These are character counts, not token usage; timing varies with the resume, posting access, and configured model.

Resume text and job details are sent to the selected AI provider for analysis. Uploads and results stay in `output/reviews/uploads/` until you remove them; this folder is excluded from Git. Keep the local server running while reviewing. One analysis runs at a time. The existing extraction and pre-generated review commands still work.

### Skill shortcuts and AI selection

- **Codex:** `$resume-review` uses the repository skill registered in `.agents/skills/resume-review` and opens the upload screen with Codex selected.
- **Claude Code:** `/resume-review` uses `.claude/skills/resume-review` and opens the same screen with Claude selected.
- **Cursor:** its resume-review skill launches with `--provider cursor`, using Cursor Agent CLI and the user’s Cursor account.
- **GitHub Copilot:** the resume-writer agent/shared skill launches with `--provider copilot`, using GitHub Copilot CLI and the user’s GitHub account.
- **Unknown terminals:** choose the desired installed AI tool on the screen.

Start a new host session if the new shortcut is not visible. For manual launch, use `--provider codex --open`, `--provider claude --open`, `--provider cursor --open`, or `--provider copilot --open`. Without an explicit provider, an unambiguous terminal marker selects it; otherwise the screen asks. The screen distinguishes a missing executable from an installed tool; sign-in is checked when review begins. **Change job** retains the original provider. See [.github/skills/resume-review/references/provider-setup.md](.github/skills/resume-review/references/provider-setup.md) for setup and adapter details. Do not share localhost links with other users; they launch their own local server.

## PDF Download Setup
The npm `preview` command handles this automatically. For direct Python use, install these dependencies in the same environment as the preview server:
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

```text
Resume/
├── README.md
├── README.ko.md
├── package.json                        # npm package and command
├── bin/resume-writer.mjs                # Command entry point
├── lib/                                # CLI and automatic runtime setup
├── requirements.txt                    # Core Python dependencies
├── .agents/skills/                     # Codex links to the shared skills
├── .claude/
│   ├── commands/resume-writer.md        # Existing Claude command
│   └── skills/                         # Writing link and review launcher
├── .cursor/
│   ├── rules/resume-writer.mdc          # Cursor agent rule
│   └── skills/                         # Writing link and review launcher
├── .github/
│   ├── agents/resume-writer.agent.md    # Copilot agent
│   └── skills/
│       ├── resume-review/
│       │   ├── SKILL.md
│       │   ├── references/             # Review rubric and provider setup
│       │   ├── scripts/                # Upload app, renderer, and tests
│       │   └── templates/              # Upload screen and review styles
│       └── resume-writing/
│           ├── SKILL.md
│           ├── references/             # Writing guidelines
│           ├── requirements-pdf.txt
│           ├── scripts/                # Preview server, converters, and tests
│           └── templates/              # Editable HTML template
├── Jennifer_Lauren_Resume.md            # Fictional content example
└── output/reviews/uploads/             # Local review data (Git-ignored)
```

The `.github/skills` directories contain the shared implementations. Preserve symbolic links when cloning, or copy the complete shared skill folder into the appropriate host's skill directory. Copying only `SKILL.md` omits the scripts and templates.
