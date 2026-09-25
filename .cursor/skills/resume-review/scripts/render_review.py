#!/usr/bin/env python3
"""Run the canonical resume review renderer from the Cursor skill."""

from pathlib import Path
import runpy


SCRIPT = Path(__file__).resolve().parents[4] / ".github/skills/resume-review/scripts/render_review.py"
runpy.run_path(str(SCRIPT), run_name="__main__")