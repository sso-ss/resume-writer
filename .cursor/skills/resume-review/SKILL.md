---
name: resume-review
description: Reviews uploaded Product Designer resumes against a target job and generates annotated HTML with requirement matches, highlighted issues, bullet-level alignment, and evidence-based revisions. Use for resume review, critique, job matching, feedback, or what to fix.
---

# Product Designer Resume Review

Follow the canonical workflow in [.github/skills/resume-review/SKILL.md](../../../.github/skills/resume-review/SKILL.md).

Run the Cursor wrapper with the same arguments:

```bash
python3 .cursor/skills/resume-review/scripts/render_review.py <resume-file> --extract
python3 .cursor/skills/resume-review/scripts/render_review.py <resume-file> <review-json> --serve
```