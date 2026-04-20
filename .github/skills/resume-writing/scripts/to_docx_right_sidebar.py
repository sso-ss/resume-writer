#!/usr/bin/env python3
"""Convert a Markdown resume to a two-column .docx — Layout C (right sidebar).

Layout C: Full-width header + right sidebar
────────────────────────────────────────────
┌──────────────────────────────────────────────────────┐
│  JENNIFER LAUREN                    Portfolio | LI   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
├─────────────────────────────────────┬────────────────┤
│  SUMMARY                      65%  │ CONTACT   35%  │
│  3 lines of summary text           │ Email          │
│                                    │ Location       │
│  EXPERIENCE                        │                │
│  Role | Company | Dates            │ SKILLS         │
│  • bullet with metric              │ Design: ...    │
│  • bullet with metric              │ Research: ...  │
│                                    │ Collab: ...    │
│  Role | Company | Dates            │                │
│  • bullet                          │ TOOLS          │
│  • bullet                          │ Figma, ...     │
│                                    │                │
│  KEY PROJECTS                      │ EDUCATION      │
│  ■ Project — impact. Link          │ Degree | Uni   │
│  ■ Project — impact. Link          │                │
└─────────────────────────────────────┴────────────────┘

Follows F-pattern: main content left (eyes land here first),
metadata on the right. Full-width name + portfolio strip with rule.

Usage:
    python to_docx_right_sidebar.py <input.md> [output.docx]

Requires: python-docx (pip install python-docx)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

try:
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    print("Error: python-docx is required. Install it with: pip install python-docx")
    sys.exit(1)

from docx_shared import (
    ACCENT, FONT, MAIN_W, SIDEBAR_BG, SIDEBAR_W,
    TEXT_BODY, TEXT_DARK, TEXT_MUTED,
    add_bottom_rule, heading, parse_contact_items, parse_markdown,
    remove_table_borders, render_main_content,
    render_sidebar_skills, set_cell_margins, set_cell_shading,
    sidebar_lines,
)


def build_layout_c(md_path: str, docx_path: Optional[str] = None) -> str:
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
    sec.left_margin = Inches(0.4)
    sec.right_margin = Inches(0.4)

    style = doc.styles["Normal"]
    style.font.name = FONT
    style.font.size = Pt(10)
    style.font.color.rgb = TEXT_BODY
    style.paragraph_format.space_after = Pt(0)
    style.paragraph_format.space_before = Pt(0)

    # ── Full-width header: Name left, portfolio right ──
    header_table = doc.add_table(rows=1, cols=2)
    header_table.autofit = False
    left_h, right_h = header_table.rows[0].cells
    left_h.width = Inches(4.5)
    right_h.width = Inches(2.7)

    # Name (left)
    p = left_h.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run(name or "Full Name")
    r.bold = True
    r.font.size = Pt(22)
    r.font.color.rgb = TEXT_DARK
    r.font.name = FONT

    # Portfolio + LinkedIn (right, top-aligned)
    p = right_h.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.paragraph_format.space_before = Pt(6)
    portfolio = ""
    linkedin = ""
    for label, value in contact_items:
        if label.lower() == "portfolio":
            portfolio = value
        elif label.lower() == "linkedin":
            linkedin = value
    links = [x for x in [portfolio, linkedin] if x]
    if links:
        r = p.add_run(" | ".join(links))
        r.font.size = Pt(8.5)
        r.font.color.rgb = ACCENT
        r.font.name = FONT

    remove_table_borders(header_table)

    # ── Horizontal rule under header ──
    rule = doc.add_paragraph()
    rule.paragraph_format.space_before = Pt(4)
    rule.paragraph_format.space_after = Pt(4)
    add_bottom_rule(rule)

    # ── Two-column body: main left, sidebar right ──
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    main, sidebar = table.rows[0].cells  # NOTE: main is LEFT, sidebar is RIGHT
    main.width = MAIN_W
    sidebar.width = SIDEBAR_W

    set_cell_shading(sidebar, SIDEBAR_BG)
    set_cell_margins(sidebar, top=120, start=140, bottom=120, end=100)
    set_cell_margins(main, top=80, start=60, bottom=80, end=160)

    # ── Right sidebar ──
    # Contact (email + location only, portfolio/linkedin are in header)
    remaining_contact = [
        (l, v) for l, v in contact_items
        if l.lower() not in ("portfolio", "linkedin")
    ]
    if remaining_contact:
        heading(sidebar, "Contact")
        for label, value in remaining_contact:
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

    # Education
    if "education" in sections:
        heading(sidebar, "Education")
        sidebar_lines(sidebar, sections["education"])

    # ── Left main column ──
    render_main_content(main, sections)

    remove_table_borders(table)
    doc.save(docx_path)
    return docx_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python to_docx_right_sidebar.py <input.md> [output.docx]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    result = build_layout_c(input_path, output_path)
    print(f"Layout C (right-sidebar) resume saved to: {result}")
