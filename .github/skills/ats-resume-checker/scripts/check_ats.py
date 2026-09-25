#!/usr/bin/env python3
"""Estimate ATS structural compatibility for Markdown and Word resumes."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"w": WORD_NS, "r": REL_NS}
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
STANDARD_SECTIONS = {
    "experience": ("experience", "work experience", "professional experience"),
    "education": ("education",),
    "skills": ("skills", "skills & tools", "skills and tools"),
}


@dataclass(frozen=True)
class Finding:
    severity: str
    rule: str
    message: str
    fix: str
    penalty: int


def add_finding(
    findings: list[Finding],
    severity: str,
    rule: str,
    message: str,
    fix: str,
    penalty: int,
) -> None:
    findings.append(Finding(severity, rule, message, fix, penalty))


def xml_text(root: ET.Element) -> str:
    blocks: list[str] = []
    for paragraph in root.findall(".//w:p", NS):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", NS))
        if text.strip():
            blocks.append(text.strip())
    return "\n".join(blocks)


def parse_xml(data: bytes) -> ET.Element:
    return ET.fromstring(data)


def has_standard_section(text: str, aliases: Iterable[str]) -> bool:
    lines = {re.sub(r"[^a-z& ]", "", line.lower()).strip() for line in text.splitlines()}
    return any(alias in lines for alias in aliases)


def portfolio_urls(text: str) -> list[str]:
    urls = re.findall(r"(?:https?://|www\.)[^\s|]+", text, flags=re.IGNORECASE)
    return [url.rstrip(".,;)") for url in urls if "linkedin.com" not in url.lower()]


def check_common(text: str, filename: str, findings: list[Finding]) -> None:
    for section, aliases in STANDARD_SECTIONS.items():
        if not has_standard_section(text, aliases):
            add_finding(
                findings,
                "high",
                f"missing-{section}-heading",
                f"No standard {section.title()} heading was detected.",
                f"Add a plain '{section.title()}' heading in the document body.",
                10,
            )

    if not portfolio_urls(text):
        add_finding(
            findings,
            "high",
            "missing-portfolio-url",
            "No complete non-LinkedIn portfolio URL was detected.",
            "Place a complete https:// portfolio URL first in the contact line.",
            12,
        )

    if not re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text):
        add_finding(
            findings,
            "high",
            "missing-email",
            "No valid email address was detected.",
            "Add a plain-text email address near the name.",
            10,
        )

    if not re.match(r"^[A-Za-z0-9]+_[A-Za-z0-9]+_.*Resume\.(?:docx|md)$", filename):
        add_finding(
            findings,
            "low",
            "filename",
            "The filename does not follow a recruiter-friendly name and role pattern.",
            "Use FirstName_LastName_ProductDesigner_Resume followed by the extension.",
            2,
        )


def check_docx(path: Path) -> tuple[str, list[Finding]]:
    findings: list[Finding] = []
    try:
        with zipfile.ZipFile(path) as archive:
            document_root = parse_xml(archive.read("word/document.xml"))
            text_parts = [xml_text(document_root)]

            table_count = len(document_root.findall(".//w:tbl", NS))
            multi_column_tables = 0
            for table in document_root.findall(".//w:tbl", NS):
                max_cells = max(
                    (len(row.findall("./w:tc", NS)) for row in table.findall("./w:tr", NS)),
                    default=0,
                )
                if max_cells > 1:
                    multi_column_tables += 1

            if multi_column_tables:
                add_finding(
                    findings,
                    "critical",
                    "multi-column-table",
                    f"Detected {multi_column_tables} table(s) used with multiple columns. ATS reading order may interleave or omit cells.",
                    "Rebuild the application version as one column using normal paragraphs and tab stops only.",
                    30,
                )
            elif table_count:
                add_finding(
                    findings,
                    "medium",
                    "table-layout",
                    f"Detected {table_count} table(s). Even single-cell tables can parse inconsistently.",
                    "Replace layout tables with normal paragraphs where possible.",
                    8,
                )

            column_sections = 0
            for columns in document_root.findall(".//w:cols", NS):
                count = int(columns.get(f"{{{WORD_NS}}}num", "1"))
                if count > 1:
                    column_sections += 1
            if column_sections:
                add_finding(
                    findings,
                    "critical",
                    "page-columns",
                    f"Detected {column_sections} true multi-column section(s).",
                    "Use a single-column page layout for the ATS version.",
                    30,
                )

            text_boxes = len(document_root.findall(".//w:txbxContent", NS))
            if text_boxes:
                add_finding(
                    findings,
                    "critical",
                    "text-boxes",
                    f"Detected {text_boxes} text box(es), which some ATS parsers ignore.",
                    "Move all text into normal body paragraphs.",
                    25,
                )

            drawings = len(document_root.findall(".//w:drawing", NS)) + len(
                document_root.findall(".//w:pict", NS)
            )
            if drawings:
                add_finding(
                    findings,
                    "medium",
                    "graphics",
                    f"Detected {drawings} drawing or image object(s). Their content is not reliably machine-readable.",
                    "Remove icons, charts, photos, and graphical text from the ATS version.",
                    8,
                )

            header_footer_text: list[str] = []
            for name in archive.namelist():
                if re.fullmatch(r"word/(?:header|footer)\d+\.xml", name):
                    part_text = xml_text(parse_xml(archive.read(name)))
                    if part_text:
                        header_footer_text.append(part_text)
                        text_parts.append(part_text)
            if header_footer_text:
                add_finding(
                    findings,
                    "medium",
                    "header-footer-content",
                    "Text was detected in a header or footer, where contact details may be skipped.",
                    "Keep essential resume content in the main document body.",
                    8,
                )

            tiny_runs = 0
            for run in document_root.findall(".//w:r", NS):
                if not run.findall(".//w:t", NS):
                    continue
                size = run.find("./w:rPr/w:sz", NS)
                if size is not None:
                    value = size.get(f"{{{WORD_NS}}}val")
                    if value and value.isdigit() and int(value) < 18:
                        tiny_runs += 1
            if tiny_runs:
                add_finding(
                    findings,
                    "low",
                    "small-type",
                    "Font sizes below 9 pt were detected, reducing recruiter scanability.",
                    "Keep body text at 9-11 pt and reserve smaller type for nonessential labels.",
                    3,
                )

            text = "\n".join(text_parts)
    except (KeyError, ET.ParseError, zipfile.BadZipFile) as error:
        raise ValueError(f"Could not read Word document structure: {error}") from error

    check_common(text, path.name, findings)
    return text, findings


def check_markdown(path: Path) -> tuple[str, list[Finding]]:
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []

    if re.search(r"^\s*\|.+\|\s*$", text, flags=re.MULTILINE):
        add_finding(
            findings,
            "medium",
            "markdown-table",
            "A Markdown table was detected and may become a Word layout table during export.",
            "Use headings and plain paragraphs for resume content.",
            8,
        )

    if not re.search(r"^#\s+\S+", text, flags=re.MULTILINE):
        add_finding(
            findings,
            "medium",
            "missing-name-heading",
            "No top-level name heading was detected.",
            "Start the document with '# FirstName LastName'.",
            6,
        )

    check_common(text, path.name, findings)
    return text, findings


def compatibility_band(score: int) -> str:
    if score >= 90:
        return "High"
    if score >= 75:
        return "Moderate"
    return "Low"


def analyze(path: Path) -> dict:
    if not path.exists():
        raise ValueError(f"File not found: {path}")
    if path.suffix.lower() == ".docx":
        _, findings = check_docx(path)
    elif path.suffix.lower() == ".md":
        _, findings = check_markdown(path)
    else:
        raise ValueError("Supported file types are .docx and .md")

    findings.sort(key=lambda item: (SEVERITY_ORDER[item.severity], item.rule))
    score = max(0, 100 - sum(item.penalty for item in findings))
    return {
        "file": str(path),
        "score": score,
        "band": compatibility_band(score),
        "verdict": "Safe for ATS upload" if score >= 90 else "Revise before ATS upload",
        "findings": [asdict(item) for item in findings],
    }


def print_report(result: dict) -> None:
    print(f"ATS compatibility: {result['score']}/100 ({result['band']})")
    print(f"Verdict: {result['verdict']}")
    if not result["findings"]:
        print("No structural risks detected by this checker.")
        return
    print("\nFindings:")
    for finding in result["findings"]:
        print(f"- [{finding['severity'].upper()}] {finding['message']}")
        print(f"  Fix: {finding['fix']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("resume", type=Path, help="Path to a .docx or .md resume")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 1 unless compatibility is High",
    )
    args = parser.parse_args()

    try:
        result = analyze(args.resume)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_report(result)
    return 1 if args.strict and result["score"] < 90 else 0


if __name__ == "__main__":
    raise SystemExit(main())