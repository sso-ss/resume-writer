---
name: resume-review
description: Open the Resume Review upload screen using Claude Code, or review a supplied resume against a target job with annotated feedback across professions.
---

# Resume Review

Follow the shared skill at [../../../.github/skills/resume-review/SKILL.md](../../../.github/skills/resume-review/SKILL.md).

For `/resume-review` or a request to open the review screen, start the existing upload application with Claude Code selected:

```bash
python3 .github/skills/resume-review/scripts/render_review.py --provider claude --open
```

Prefer the project's `.venv/bin/python` when available. Resolve the repository path from this skill's location if the working directory differs. Keep the server running. If the host has a browser panel, omit `--open` and open the printed URL there instead. The user adds their resume and job inside that screen; do not ask for the posting before opening it. Claude Code must be installed and signed in. Never launch with Codex selected on behalf of a Claude user unless they request it.

For explicit direct analysis, extraction, or rendering, follow the shared skill's chat workflow.
