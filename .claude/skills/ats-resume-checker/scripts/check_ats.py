#!/usr/bin/env python3
"""Run the canonical ATS resume checker from the Claude skill."""

from pathlib import Path
import runpy


SCRIPT = Path(__file__).resolve().parents[4] / ".github/skills/ats-resume-checker/scripts/check_ats.py"
runpy.run_path(str(SCRIPT), run_name="__main__")