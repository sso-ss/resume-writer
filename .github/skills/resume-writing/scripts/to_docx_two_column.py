#!/usr/bin/env python3
"""Convert a Markdown resume to a two-column .docx — Layout B (sidebar-left).

Layout B: Name anchored inside left sidebar
────────────────────────────────────────────
┌────────────────┬─────────────────────────────────────┐
│  JENNIFER      │                                     │
│  LAUREN        │  SUMMARY                            │
│  ─────────     │  3 lines full width in main col     │
│  CONTACT       │                                     │
│  Portfolio     │  EXPERIENCE                         │
│  LinkedIn      │  Role | Company | Dates             │
│  Email         │  • bullet                           │
│  Location      │  • bullet                           │
│  ─────────     │                                     │
│  SKILLS        │  Role | Company | Dates             │
│  Design: ...   │  • bullet                           │
│  Research: ... │  • bullet                           │
│  ─────────     │                                     │
│  EDUCATION     │  KEY PROJECTS                       │
│  Degree, Uni   │  ■ Project + link                   │
│  ─────────     │  ■ Project + link                   │
│  TOOLS         │                                     │
│  Figma, ...    │                                     │
└────────────────┴─────────────────────────────────────┘

Name lives inside sidebar — anchored, not floating. Everything static
in the left, everything narrative on the right.

Usage:
    python to_docx_two_column.py <input.md> [output.docx]

Requires: python-docx (pip install python-docx)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

try:
    from docx import Document
    from docx.shared import Inches, Pt
except ImportError:
    print("Error: python-docx is required. Install it with: pip install python-docx")
    sys.exit(1)

from docx_shared import (
    ACCENT, FONT, MAIN_W, SIDEBAR_BG, SIDEBAR_W,
    TEXT_BODY, TEXT_DARK, TEXT_MUTED,
    heading, parse_contact_items, parse_markdown,
    remove_table_borders, render_main_content,
    render_sidebar_skills, set_cell_margins, set_cell_shading,
    sidebar_lines,
)


def build_layout_b(md_path: str, docx_path: Optional[str] = None) -> str:
    md_file = Path(md_path)
    if not md_file.exists():
        print(f"Error: {md_path} not found")
        sys.exit(1)

    if docx_path is None:
        base = md_file.stem.replace("_Resume", "")
        docx_path = str(md_file.with_name(f"{base}_ProductDesigner_Resume.docx"))

    name, contact_line, sections = parse_markdown(md_file.read_text(encoding="utf-8"))
    contact_items = parse_contact_items(contact_line) if contact_line else []

    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Inches(0.4)
    sec.bottom_margin = Inches(0.4)
    sec.left_margin = Inches(0.35)
    sec.right_margin = Inches(0.35)

    style = doc.styles["Normal"]
    style.font.name = FONT
    style.font.size = Pt(10)
    style.font.color.rgb = TEXT_BODY
    style.paragraph_format.space_after = Pt(0)
    style.paragraph_format.space_before = Pt(0)

    # Full-width table, one row
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    sidebar, main = table.rows[0].cells
    sidebar.width = SIDEBAR_W
    main.width = MAIN_W

    set_cell_shading(sidebar, SIDEBAR_BG)
    set_cell_margins(sidebar, top=140, start=140, bottom=140, end=100)
    set_cell_margins(main, top=140, start=180, bottom=140, end=80)

    # ── Sidebar: Name inside ──
    # Split name into first/last for stacked display
    parts = (name or "Full Name").split(None, 1)
    first_name = parts[0] if parts else ""
    last_name = parts[1] if len(parts) > 1 else ""

    p = sidebar.paragraphs[0]  # use the default empty paragraph
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run(first_name)
    r.bold = True
    r.font.size = Pt(20)
    r.font.color.rgb = TEXT_DARK
    r.font.name = FONT

    if last_name:
        p = sidebar.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(6)
        r = p.add_run(last_name)
        r.bold = True
        r.font.size = Pt(20)
        r.font.color.rgb = TEXT_DARK
        r.font.name = FONT

    # Thin separator
    p = sidebar.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("─" * 18)
    r.font.size = Pt(6)
    r.font.color.rgb = TEXT_MUTED
    r.font.name = FONT

    # Contact
    if contact_items:
        heading(sidebar, "Contact")
        for label, value in contact_items:
            p = sidebar.add_paragraph()
            p.paragraph_format.space_after = Pt(1)
            r = p.add_run(f"{label}\n")
            r.font.size = Pt(7)
            r.font.color.rgb = TEXT_MUTED
            r.font.name = FONT
            r.bold = True
            r = p.add_run(value)
            r.font.size = Pt(8.5)
            r.font.color.rgb = TEXT_DARK
            r.font.name = FONT

    # Skills & Tools
    render_sidebar_skills(sidebar, sections)

    # Separator
    p = sidebar.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("─" * 18)
    r.font.size = Pt(6)
    r.font.color.rgb = TEXT_MUTED

    # Education
    if "education" in sections:
        heading(sidebar, "Education")
        sidebar_lines(sidebar, sections["education"])

    # ── Main column ──
    render_main_content(main, sections)

    remove_table_borders(table)
    doc.save(docx_path)
    return docx_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python to_docx_two_column.py <input.md> [output.docx]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    result = build_layout_b(input_path, output_path)
    print(f"Layout B (two-column) resume saved to: {result}")
