# Resume Review connections

The upload app supports Codex CLI, Claude Code, Cursor Agent CLI, and GitHub Copilot CLI. Each request starts a separate noninteractive analysis using the selected installed CLI's account and configured model. It does not inherit conversation history or automatically inherit a model selected only in the parent session. It never falls back to another provider.

## Setup

- Install Python 3 and `python-docx` in the environment that runs the server. PDF uploads also need `pypdf`. For an isolated setup: `python3 -m venv .venv`, then `.venv/bin/python -m pip install python-docx 'pypdf>=5,<7'` (Windows: `.venv\Scripts\python`).
- [Codex CLI](https://developers.openai.com/codex/cli/): install Codex, run `codex`, and finish sign-in. `codex` must be on the server's PATH.
- [Claude Code](https://code.claude.com/docs/en/overview): install a current Claude Code version, run `claude`, and finish sign-in. `claude` must be on the server's PATH. The adapter requires print mode, JSON schema output, tool restrictions, and session controls; update older versions if these options are unavailable.
- [Cursor Agent CLI](https://cursor.com/docs/cli/overview): install the CLI (`agent` or `cursor-agent` on PATH), then run `agent login` with your Cursor account. The desktop editor launcher alone is insufficient.
- [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/cli-getting-started): install `copilot`, run it, and sign in with your GitHub account and Copilot access. VS Code extension sign-in alone is not a CLI setup check.
- Existing supported CLI authentication is reused. No separate key is collected by this app. Provider subscriptions, configured API credentials, organizational settings, and usage limits still apply.

## Launch

From this repository, choose the matching command:

```bash
python3 .github/skills/resume-review/scripts/render_review.py --provider codex --open
python3 .github/skills/resume-review/scripts/render_review.py --provider claude --open
python3 .github/skills/resume-review/scripts/render_review.py --provider cursor --open
python3 .github/skills/resume-review/scripts/render_review.py --provider copilot --open
```

Omit `--open` when the AI host opens the printed URL in its own browser panel. Keep the server running. Outputs are saved under `output/reviews/uploads/` relative to the launch working directory.

For an installed canonical skill, run `scripts/render_review.py` relative to its actual directory. This repository uses regular launcher files in `.agents/skills`, `.claude/skills`, and `.cursor/skills`; Copilot reads the canonical `.github/skills` files. Launchers load the complete shared workflow and resolve resources in its directory. Manual project searches must include hidden directories (`rg --files --hidden`).

Run `python3 bin/register-skills.py` to register both skills in the four tools' personal skill folders, or add `--host claude`, `--host cursor`, `--host copilot`, or `--host codex` for one tool. The personal launchers refer to this checkout by absolute path; keep it available and rerun registration if it moves. Existing custom entries are preserved. `--scope project` repairs the known legacy project links. Start a new host session if the new skill is not discovered immediately. For a standalone transfer without this checkout, copy the entire canonical skill folder, not just `SKILL.md`, and select the current host's explicit provider.

`--provider auto` recognizes an unambiguous `CODEX_THREAD_ID` or `CLAUDECODE` marker. When neither or both are present, users choose a provider on the page. Cursor and Copilot skill launchers pass an explicit provider; the app does not guess those hosts from installation or generic terminal variables. Executable detection is not proof of sign-in: the selected CLI checks account access when analysis starts. A missing executable disables submission and shows setup instructions; an account or service failure is shown with retry guidance. Change job reuses the saved provider; old reviews without provider metadata are Codex reviews.

Cursor and Copilot use their own CLI integrations and accounts. These are separate analysis sessions; the app cannot borrow an editor conversation or guarantee its exact model selection. Other terminals can choose any installed supported CLI.

## Adapter behavior

- Codex uses its read-only noninteractive mode and structured response schema.
- Claude uses [print mode with structured outputs](https://code.claude.com/docs/en/headless). Only WebFetch and WebSearch are available for reading the supplied public posting; shell/edit tools, skills, hooks, and configured MCP servers are disabled for this analysis. No permission-bypass flag is used. User settings remain available for authentication/model configuration. Managed organization policy can still apply.
- Cursor uses [headless JSON output](https://cursor.com/docs/cli/reference/output-format) in Ask mode with the sandbox enabled. The temporary workspace’s [CLI permissions](https://cursor.com/docs/cli/reference/permissions) deny shell, reads, writes, and MCP calls while allowing web fetch. `--trust` applies only to this freshly created analysis workspace; no force/yolo flag is used.
- Copilot uses [noninteractive output](https://docs.github.com/en/copilot/reference/cli-command-reference), exposing only `web_fetch`, denying shell/read/write, disabling built-in MCP servers and remote exports. No blanket tool-approval flag is used.
- Cursor and Copilot return text that is parsed and schema-validated locally, in addition to evidence validation. Malformed output fails safely rather than being displayed as a completed review. Keep each CLI current if an option is unsupported.
- All receive the same concise review rubric and block references and pass through identical evidence/coverage validation. Resume and job text are untrusted input.
- CLI logs are not returned to the browser. Uploads, review results, and provider/timing metadata are saved locally; provider-side handling follows the user's chosen service.
