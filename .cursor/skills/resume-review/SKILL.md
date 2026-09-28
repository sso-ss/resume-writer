---
name: resume-review
description: Open the Resume Review upload screen, or review a supplied resume against a target job with annotated, evidence-based feedback across professions.
---

# Resume Review

Follow [../../../.github/skills/resume-review/SKILL.md](../../../.github/skills/resume-review/SKILL.md).

For a request to open Resume Review, start the canonical upload app and open the printed URL:

```bash
python3 .github/skills/resume-review/scripts/render_review.py --provider cursor --open
```

Prefer the project's `.venv/bin/python` when available. Resolve the repository path from this skill's location when launched elsewhere. Keep the server running. If the host has a browser panel, omit `--open` and open the printed URL there. The user supplies the resume and posting in that screen.

The screen uses Cursor Agent CLI with the user’s Cursor account. If it is missing, guide the user to install Cursor Agent CLI and run `agent login`; editor sign-in alone may not sign in the CLI. Do not silently substitute a provider. For a direct review in chat, follow the canonical skill's chat workflow.
