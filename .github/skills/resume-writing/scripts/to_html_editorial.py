#!/usr/bin/env python3
"""Render a Markdown resume in the editable editorial HTML layout."""

from __future__ import annotations

import hashlib
import re
import sys
from html import escape
from pathlib import Path
from string import Template
from typing import Optional

from docx_shared import parse_contact_items, parse_markdown


TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "editorial-right.html"
WORD_EXPORT = Path(__file__).with_name("word-export.js")


def inline(text: str) -> str:
    parts = re.split(r"(\*\*[^*]+\*\*)", text)
    return "".join(
        f"<strong>{escape(part[2:-2])}</strong>"
        if part.startswith("**") and part.endswith("**") else escape(part)
        for part in parts
    )


def section(title: str, content: str, class_name: str = "section") -> str:
    return f'<section class="{class_name}" data-section="{title}"><h2>{title}</h2>{content}</section>' if content else ""


def jobs_html(lines: list[str]) -> str:
    jobs: list[str] = []
    title = company = dates = ""
    bullets: list[str] = []

    def append_job() -> None:
        if not title:
            return
        items = "".join(f"<li>{inline(bullet)}</li>" for bullet in bullets)
        company_html = f' | <span class="org">{escape(company)}</span>' if company else ""
        jobs.append(
            '<article class="job"><div class="job-header">'
            f"<h3>{escape(title)}{company_html}</h3>"
            f"<p class=\"meta\">{escape(dates)}</p></div><ul>{items}</ul></article>"
        )

    for raw in lines:
        line = raw.strip()
        if line.startswith("### "):
            append_job()
            parts = [part.strip() for part in line[4:].split("|")]
            title = parts[0]
            company = parts[1] if len(parts) > 1 else ""
            dates = parts[2] if len(parts) > 2 else ""
            bullets = []
        elif line.startswith("- ") and title:
            bullets.append(line[2:])
    append_job()
    return "".join(jobs)


def projects_html(lines: list[str]) -> str:
    projects: list[str] = []
    for raw in lines:
        match = re.match(r"-\s+\*\*(.*?)\*\*\s+[—-]\s+(.+)", raw.strip())
        if not match:
            continue
        title, detail = match.groups()
        description, marker, case_study = detail.partition("Case study:")
        link = case_study.strip()
        if link.startswith(("https://", "http://")):
            href = f'<a href="{escape(link, quote=True)}" rel="noopener noreferrer">{escape(link)}</a>'
        else:
            href = escape(link)
        case_study_html = f'<p class="portfolio">Case study: {href}</p>' if marker else ""
        projects.append(
            '<article class="project">'
            f"<h3>{escape(title)}</h3><p>{inline(description.strip())}</p>"
            f"{case_study_html}</article>"
        )
    return "".join(projects)


def skills_html(lines: list[str]) -> tuple[str, str]:
    skills: list[str] = []
    tools = ""
    for raw in lines:
        match = re.match(r"-\s+\*\*(.*?)\*\*\s*(.*)", raw.strip())
        if not match:
            continue
        label, values = match.groups()
        if label.rstrip(":").lower() == "tools":
            tools = f"<p>{escape(values)}</p>"
        else:
            skills.append(f'<p><span class="label">{escape(label.rstrip(":"))}</span>{escape(values)}</p>')
    return "".join(skills), tools


def contact_html(contact_line: str) -> str:
    items = parse_contact_items(contact_line)
    items.sort(key=lambda item: 0 if item[0].lower() == "portfolio" else 1)
    spans: list[str] = []
    for label, value in items:
        label_text = "Portfolio: " if label.lower() == "portfolio" else ""
        if value.startswith(("https://", "http://")):
            content = f'<a href="{escape(value, quote=True)}" rel="noopener noreferrer">{escape(value)}</a>'
        elif label.lower() == "email":
            content = f'<a href="mailto:{escape(value, quote=True)}">{escape(value)}</a>'
        else:
            content = escape(value)
        spans.append(f"<span>{label_text}{content}</span>")
    return "".join(spans)


def build_html(md_path: str, html_path: Optional[str] = None, layout: str = "editorial-html") -> str:
    md_file = Path(md_path)
    if not md_file.is_file():
        raise FileNotFoundError(f"Resume not found: {md_path}")
    valid_layouts = {
        "single-column", "two-column-left", "two-column-right",
        "two-column-right-refined", "editorial-html",
    }
    if layout not in valid_layouts:
        raise ValueError(f"Unknown resume layout: {layout}")
    if html_path is None:
        base = md_file.stem.replace("_Resume", "")
        suffix = "Editorial" if layout == "editorial-html" else "Preview"
        html_path = str(md_file.with_name(f"{base}_ProductDesigner_Resume_{suffix}.html"))

    source = md_file.read_text(encoding="utf-8")
    name, contact_line, sections = parse_markdown(source)
    summary = " ".join(line.strip() for line in sections.get("summary", []) if line.strip())
    role = summary.split(" with ", 1)[0] if " with " in summary else "Product Designer"
    experience = section("Experience", jobs_html(sections.get("experience", [])))
    projects = section("Selected Projects", projects_html(sections.get("key projects", sections.get("projects", []))))
    expertise, tools = skills_html(sections.get("skills & tools", sections.get("skills", [])))
    expertise = section("Expertise", expertise, "aside-section")
    tools = section("Tools", tools, "aside-section")
    recognition = "".join(
        f"<p>{inline(line[2:])}</p>"
        for raw in sections.get("recognition", [])
        if (line := raw.strip()).startswith("- ")
    )
    recognition = section("Recognition", recognition, "aside-section")
    education_lines = [line.strip() for line in sections.get("education", []) if line.strip()]
    education = "".join(f"<p>{escape(line)}</p>" for line in education_lines)
    education = section("Education", education, "aside-section")

    identity = (
        '<header><p class="eyebrow">Research · Interaction · Visual design</p>'
        f'<h1>{escape(name)}</h1><p class="role">{escape(role)}</p>'
    )
    contact = f'<div class="contact">{contact_html(contact_line)}</div>'
    summary_label = '<h2 class="summary-label">Summary</h2>'
    intro = f'<p class="intro">{escape(summary)}</p>'
    main_sections = experience + projects
    sidebar_sections = expertise + tools + recognition + education
    if layout == "single-column":
        page_content = f'{identity}{contact}{summary_label}{intro}</header><div class="layout"><div>{main_sections}{sidebar_sections}</div></div>'
    elif layout == "two-column-left":
        page_content = (
            f'<div class="layout"><aside class="sidebar">{identity}{contact}{summary_label}</header>{sidebar_sections}</aside>'
            f'<div class="main-column">{intro}{main_sections}</div></div>'
        )
    elif layout == "two-column-right":
        page_content = (
            f'{identity}{summary_label}</header><div class="layout"><div class="main-column">{intro}{main_sections}</div>'
            f'<aside class="sidebar">{contact}{sidebar_sections}</aside></div>'
        )
    else:
        page_content = (
            f'{identity}{contact}{summary_label}{intro}</header><div class="layout"><div class="main-column">{main_sections}</div>'
            f'<aside class="sidebar">{sidebar_sections}</aside></div>'
        )

    html = Template(TEMPLATE.read_text(encoding="utf-8")).substitute(
        name=escape(name),
        layout=layout,
        layout_label=layout.replace("-", " ").title(),
        page_content=page_content,
        storage_key=hashlib.sha256(source.encode("utf-8")).hexdigest()[:12],
        word_export_script=WORD_EXPORT.read_text(encoding="utf-8"),
    )
    output = Path(html_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return str(output)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python to_html_editorial.py <input.md> [output.html]")
        sys.exit(1)
    print(f"Editorial HTML resume saved to: {build_html(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)}")