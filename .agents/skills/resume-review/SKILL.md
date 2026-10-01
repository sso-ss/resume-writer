---
name: resume-review
description: Reviews uploaded resumes against a target job using role-relevant criteria and generates annotated HTML with requirement matches, highlighted issues, bullet-level alignment, and evidence-based revisions. Use when a user asks to open Resume Review, review a resume, critique it, match a job, or identify what to fix. Opens the upload screen by default; also supports reviewing provided Markdown, Word, or searchable PDF files in chat.
---

<!-- Managed by bin/register-skills.py. -->

# resume-review

Read and follow the complete shared workflow at [resume-review](<../../../.github/skills/resume-review/SKILL.md>).

Resolve its scripts, references, and templates relative to the shared skill directory linked above, rather than this launcher or the current workspace. Prefer `.venv/bin/python` when available; otherwise use Python 3 with the required dependencies.

This launcher is for codex. For a request to open Resume Review, run from the repository containing this entry file:

```bash
".venv/bin/python" ".github/skills/resume-review/scripts/render_review.py" --provider codex
```

Keep the server running and open its printed URL in the host browser panel, or add `--open` for the default browser. The user supplies the resume and job in that screen. Follow the shared chat workflow for direct analysis of supplied files. If this entry is read by another supported host, use that host's explicit provider as required by the shared skill; never substitute a provider silently.
