#!/usr/bin/env python3
"""Render an annotated HTML review for a Markdown or Word resume."""

from __future__ import annotations

import argparse
import json
import re
import secrets
import sys
from dataclasses import dataclass
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


SEVERITIES = ("critical", "important", "polish")
BULLET_RATINGS = ("strong", "needs-work")
JOB_MATCH_STATUSES = ("strong-match", "partial-match", "gap")
BULLET_JOB_ALIGNMENTS = ("strong-match", "partial-match", "not-relevant")
JOB_PRIORITIES = ("core", "preferred")
PASTED_JOB_SOURCE = "User-provided job description"
REVIEWED_BULLET_SECTIONS = {
    "experience", "work experience", "professional experience",
    "projects", "key projects", "selected projects",
}
SECTION_HEADINGS = {
    "summary", "experience", "work experience", "professional experience",
    "projects", "key projects", "selected projects", "education", "skills",
    "skills & tools", "skills and tools", "tools", "recognition", "volunteer",
}


@dataclass(frozen=True)
class Block:
    text: str
    kind: str
    section: str


def visible_markdown(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    return text.replace("**", "").replace("__", "").strip()


def markdown_blocks(path: Path) -> list[Block]:
    blocks: list[Block] = []
    section = "Header"
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# "):
            blocks.append(Block(visible_markdown(line[2:]), "name", "Header"))
        elif line.startswith("## "):
            section = visible_markdown(line[3:])
            blocks.append(Block(section, "section", section))
        elif line.startswith("### "):
            blocks.append(Block(visible_markdown(line[4:]), "role", section))
        elif re.match(r"^[-*]\s+", line):
            blocks.append(Block(visible_markdown(re.sub(r"^[-*]\s+", "", line)), "bullet", section))
        else:
            blocks.append(Block(visible_markdown(line), "paragraph", section))
    return blocks


def docx_blocks(path: Path) -> list[Block]:
    try:
        from docx import Document
        from docx.table import Table
        from docx.text.paragraph import Paragraph
    except ImportError as error:
        raise ValueError("Word review requires python-docx: python3 -m pip install python-docx") from error

    document = Document(path)
    paragraphs: list[Paragraph] = []
    for child in document.element.body.iterchildren():
        if child.tag.endswith("}p"):
            paragraphs.append(Paragraph(child, document))
        elif child.tag.endswith("}tbl"):
            table = Table(child, document)
            seen_cells: set[int] = set()
            for row in table.rows:
                for cell in row.cells:
                    identity = id(cell._tc)
                    if identity in seen_cells:
                        continue
                    seen_cells.add(identity)
                    paragraphs.extend(cell.paragraphs)

    blocks: list[Block] = []
    section = "Header"
    for paragraph in paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        style = (paragraph.style.name if paragraph.style else "").lower()
        normalized = re.sub(r"[^a-z& ]", "", text.lower()).strip()
        if normalized in SECTION_HEADINGS:
            section = text
            kind = "section"
        elif not blocks:
            kind = "name"
        elif "heading" in style:
            kind = "role"
        elif "list" in style or paragraph._p.xpath("./w:pPr/w:numPr"):
            kind = "bullet"
        else:
            kind = "paragraph"
        blocks.append(Block(text, kind, section))
    return blocks


def extract_blocks(path: Path) -> list[Block]:
    if not path.is_file():
        raise ValueError(f"Resume not found: {path}")
    if path.suffix.lower() == ".md":
        return markdown_blocks(path)
    if path.suffix.lower() == ".docx":
        return docx_blocks(path)
    raise ValueError("Supported resume types are .md and .docx")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def load_review(path: Path) -> dict:
    try:
        review = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read review JSON: {error}") from error
    target_job = review.get("target_job")
    if not isinstance(target_job, dict):
        raise ValueError("Review JSON must contain a target_job object")
    missing_job = {"title", "company", "source", "summary", "requirements"} - target_job.keys()
    if missing_job:
        raise ValueError(f"target_job is missing: {', '.join(sorted(missing_job))}")
    if not all(isinstance(target_job[key], str) and target_job[key].strip() for key in (
        "title", "company", "source", "summary"
    )):
        raise ValueError("target_job text fields must be non-empty strings")
    source = target_job["source"].strip()
    if not source.startswith(("https://", "http://")) and source != PASTED_JOB_SOURCE:
        raise ValueError(
            "target_job source must be a job posting URL or 'User-provided job description'"
        )
    requirements = target_job["requirements"]
    if not isinstance(requirements, list) or not requirements:
        raise ValueError("target_job requirements must be a non-empty array")
    for index, requirement in enumerate(requirements, 1):
        if not isinstance(requirement, dict):
            raise ValueError(f"Job requirement {index} must be an object")
        missing = {"requirement", "priority", "status", "evidence_quotes", "feedback"} - requirement.keys()
        if missing:
            raise ValueError(f"Job requirement {index} is missing: {', '.join(sorted(missing))}")
        if requirement["priority"] not in JOB_PRIORITIES:
            raise ValueError(f"Job requirement {index} priority must be one of: {', '.join(JOB_PRIORITIES)}")
        if requirement["status"] not in JOB_MATCH_STATUSES:
            raise ValueError(f"Job requirement {index} status must be one of: {', '.join(JOB_MATCH_STATUSES)}")
        if not all(isinstance(requirement[key], str) and requirement[key].strip() for key in (
            "requirement", "feedback"
        )):
            raise ValueError(f"Job requirement {index} text fields must be non-empty strings")
        if not isinstance(requirement["evidence_quotes"], list) or not all(
            isinstance(item, str) and item.strip() for item in requirement["evidence_quotes"]
        ):
            raise ValueError(f"Job requirement {index} evidence_quotes must be an array of non-empty strings")
        if requirement["status"] == "gap" and requirement["evidence_quotes"]:
            raise ValueError(f"Job requirement {index} marked gap cannot include evidence quotes")
        if requirement["status"] != "gap" and not requirement["evidence_quotes"]:
            raise ValueError(f"Job requirement {index} marked as a match needs resume evidence")
    findings = review.get("findings")
    if not isinstance(findings, list):
        raise ValueError("Review JSON must contain a findings array")
    for index, finding in enumerate(findings, 1):
        if not isinstance(finding, dict):
            raise ValueError(f"Finding {index} must be an object")
        missing = {"section", "severity", "title", "quote", "issue", "why", "suggestion"} - finding.keys()
        if missing:
            raise ValueError(f"Finding {index} is missing: {', '.join(sorted(missing))}")
        if finding["severity"] not in SEVERITIES:
            raise ValueError(f"Finding {index} severity must be one of: {', '.join(SEVERITIES)}")
        if not all(isinstance(finding[key], str) and finding[key].strip() for key in (
            "section", "title", "quote", "issue", "why", "suggestion"
        )):
            raise ValueError(f"Finding {index} fields must be non-empty strings")
    bullet_reviews = review.get("bullet_reviews")
    if not isinstance(bullet_reviews, list):
        raise ValueError("Review JSON must contain a bullet_reviews array")
    for index, bullet_review in enumerate(bullet_reviews, 1):
        if not isinstance(bullet_review, dict):
            raise ValueError(f"Bullet review {index} must be an object")
        missing = {
            "section", "quote", "rating", "assessment", "strengths", "gaps", "suggestion",
            "job_alignment", "job_feedback",
        } - bullet_review.keys()
        if missing:
            raise ValueError(f"Bullet review {index} is missing: {', '.join(sorted(missing))}")
        if bullet_review["rating"] not in BULLET_RATINGS:
            raise ValueError(
                f"Bullet review {index} rating must be one of: {', '.join(BULLET_RATINGS)}"
            )
        if bullet_review["job_alignment"] not in BULLET_JOB_ALIGNMENTS:
            raise ValueError(
                f"Bullet review {index} job_alignment must be one of: {', '.join(BULLET_JOB_ALIGNMENTS)}"
            )
        if not all(isinstance(bullet_review[key], str) and bullet_review[key].strip() for key in (
            "section", "quote", "assessment", "suggestion", "job_feedback"
        )):
            raise ValueError(f"Bullet review {index} text fields must be non-empty strings")
        for key in ("strengths", "gaps"):
            if not isinstance(bullet_review[key], list) or not all(
                isinstance(item, str) and item.strip() for item in bullet_review[key]
            ):
                raise ValueError(f"Bullet review {index} {key} must be an array of non-empty strings")
    return review


def match_findings(blocks: list[Block], findings: list[dict]) -> tuple[dict[int, list[int]], list[int]]:
    matches: dict[int, list[int]] = {}
    unmatched: list[int] = []
    for finding_index, finding in enumerate(findings):
        quote = normalize(finding["quote"])
        section = normalize(finding["section"])
        candidates = [
            block_index for block_index, block in enumerate(blocks)
            if quote in normalize(block.text) and (
                section in {"", "any", "header"} or section == normalize(block.section)
            )
        ]
        if not candidates:
            candidates = [
                block_index for block_index, block in enumerate(blocks)
                if quote in normalize(block.text)
            ]
        if candidates:
            matches.setdefault(candidates[0], []).append(finding_index)
        else:
            unmatched.append(finding_index)
    return matches, unmatched


def match_bullet_reviews(blocks: list[Block], bullet_reviews: list[dict]) -> dict[int, int]:
    reviewable = {
        block_index for block_index, block in enumerate(blocks)
        if block.kind == "bullet" and normalize(block.section) in REVIEWED_BULLET_SECTIONS
    }
    matches: dict[int, int] = {}
    unmatched: list[int] = []
    for review_index, bullet_review in enumerate(bullet_reviews):
        quote = normalize(bullet_review["quote"])
        section = normalize(bullet_review["section"])
        candidates = [
            block_index for block_index in reviewable
            if block_index not in matches
            and normalize(blocks[block_index].text) == quote
            and normalize(blocks[block_index].section) == section
        ]
        if candidates:
            matches[candidates[0]] = review_index
        else:
            unmatched.append(review_index + 1)
    if unmatched:
        raise ValueError(
            "Bullet review anchors must match one full visible bullet in the named section; "
            f"check bullet review(s): {', '.join(map(str, unmatched))}"
        )
    uncovered = sorted(reviewable - matches.keys())
    if uncovered:
        previews = "; ".join(blocks[index].text[:70] for index in uncovered[:3])
        raise ValueError(f"Every Experience and Projects bullet needs a content review. Missing: {previews}")
    return matches


def match_job_requirements(blocks: list[Block], requirements: list[dict]) -> dict[int, list[int]]:
    matches: dict[int, list[int]] = {}
    unmatched: list[tuple[int, str]] = []
    for requirement_index, requirement in enumerate(requirements):
        for quote in requirement["evidence_quotes"]:
            needle = normalize(quote)
            candidates = [
                block_index for block_index, block in enumerate(blocks)
                if needle in normalize(block.text)
            ]
            if candidates:
                matches.setdefault(candidates[0], []).append(requirement_index)
            else:
                unmatched.append((requirement_index + 1, quote))
    if unmatched:
        details = "; ".join(f"requirement {index}: {quote[:55]}" for index, quote in unmatched[:3])
        raise ValueError(f"Job-match evidence must quote visible resume text. Check {details}")
    return matches


def highlight(text: str, quotes: Iterable[str]) -> str:
    spans: list[tuple[int, int]] = []
    lowered = text.casefold()
    for quote in quotes:
        needle = quote.strip().casefold()
        start = lowered.find(needle)
        if start >= 0:
            spans.append((start, start + len(needle)))
    if not spans:
        return escape(text)
    spans.sort()
    merged: list[tuple[int, int]] = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    output: list[str] = []
    cursor = 0
    for start, end in merged:
        output.extend((escape(text[cursor:start]), "<mark>", escape(text[start:end]), "</mark>"))
        cursor = end
    output.append(escape(text[cursor:]))
    return "".join(output)


def build_html(resume_path: Path, review_path: Path, output_path: Path) -> Path:
    blocks = extract_blocks(resume_path)
    review = load_review(review_path)
    findings = review["findings"]
    bullet_reviews = review["bullet_reviews"]
    target_job = review["target_job"]
    requirements = target_job["requirements"]
    matches, unmatched = match_findings(blocks, findings)
    bullet_matches = match_bullet_reviews(blocks, bullet_reviews)
    job_matches = match_job_requirements(blocks, requirements)
    candidate = review.get("candidate") or next((block.text for block in blocks if block.kind == "name"), resume_path.stem)
    overall = review.get("overall", "Review the annotated sections and prioritize the highest-impact changes.")
    strengths = review.get("strengths", [])
    if not isinstance(strengths, list) or not all(isinstance(item, str) for item in strengths):
        raise ValueError("strengths must be an array of strings")

    document_parts: list[str] = []
    for block_index, block in enumerate(blocks):
        finding_indexes = matches.get(block_index, [])
        bullet_review_index = bullet_matches.get(block_index)
        job_requirement_indexes = job_matches.get(block_index, [])
        classes = f"resume-block {block.kind}"
        attribute_parts: list[str] = []
        badge_parts: list[str] = []
        if finding_indexes:
            classes += " annotated"
            ids = " ".join(f"note-{index + 1}" for index in finding_indexes)
            attribute_parts.append(f'data-notes="{ids}"')
            badge_parts.extend(
                f'<button type="button" class="finding-badge {escape(findings[index]["severity"])}" '
                f'data-note="note-{index + 1}" aria-label="Open annotation {index + 1}">{index + 1}</button>'
                for index in finding_indexes
            )
        if job_requirement_indexes:
            job_ids = " ".join(f"job-note-{index + 1}" for index in job_requirement_indexes)
            attribute_parts.append(f'data-job-matches="{job_ids}"')
            badge_parts.extend(
                f'<button type="button" class="job-badge" data-job-note="job-note-{index + 1}" '
                f'aria-label="Open target job match {index + 1}">J{index + 1}</button>'
                for index in job_requirement_indexes
            )
        if bullet_review_index is not None:
            bullet_review = bullet_reviews[bullet_review_index]
            rating = bullet_review["rating"]
            classes += f" bullet-reviewed bullet-{rating}"
            bullet_id = f"bullet-note-{bullet_review_index + 1}"
            attribute_parts.append(f'data-bullet-review="{bullet_id}"')
            badge_parts.append(
                f'<button type="button" class="bullet-badge {rating}" data-bullet-note="{bullet_id}" '
                f'aria-label="Open bullet content review {bullet_review_index + 1}">B{bullet_review_index + 1}</button>'
            )
        attributes = (" " + " ".join(attribute_parts) + ' tabindex="0"') if attribute_parts else ""
        badges = (
            '<span class="badges" aria-label="Resume review notes">' + "".join(badge_parts) + "</span>"
            if badge_parts else ""
        )
        content = highlight(block.text, (findings[index]["quote"] for index in finding_indexes))
        tag = {"name": "h1", "section": "h2", "role": "h3", "bullet": "li"}.get(block.kind, "p")
        document_parts.append(f'<{tag} class="{classes}"{attributes}>{content}{badges}</{tag}>')

    cards: list[str] = []
    for index, finding in enumerate(findings, 1):
        linked = index - 1 not in unmatched
        cards.append(
            f'<article class="annotation {escape(finding["severity"])}" id="note-{index}" '
            f'data-target="{index}" tabindex="0">'
            f'<div class="annotation-meta"><span>{index}</span><strong>{escape(finding["severity"])}</strong>'
            f'<small>{escape(finding["section"])}</small></div>'
            f'<h3>{escape(finding["title"])}</h3>'
            f'<p>{escape(finding["issue"])}</p>'
            f'<p class="why"><b>Why it matters</b>{escape(finding["why"])}</p>'
            f'<div class="suggestion"><b>Suggested revision</b><p>{escape(finding["suggestion"])}</p></div>'
            + ("" if linked else '<p class="unmatched">Anchor not found. Check the quoted text.</p>')
            + "</article>"
        )

    bullet_cards: list[str] = []
    for index, bullet_review in enumerate(bullet_reviews, 1):
        strengths_list = "".join(f"<li>{escape(item)}</li>" for item in bullet_review["strengths"])
        gaps_list = "".join(f"<li>{escape(item)}</li>" for item in bullet_review["gaps"])
        gaps_html = (
            f'<div class="bullet-detail gaps"><b>Content gaps</b><ul>{gaps_list}</ul></div>'
            if gaps_list else ""
        )
        bullet_cards.append(
            f'<article class="bullet-review {escape(bullet_review["rating"])}" id="bullet-note-{index}" tabindex="0">'
            f'<div class="bullet-review-meta"><span class="review-tag {escape(bullet_review["rating"])}">B{index}</span><strong>{escape(bullet_review["rating"].replace("-", " "))}</strong>'
            f'<small>{escape(bullet_review["section"])}</small></div>'
            f'<p class="bullet-quote">{escape(bullet_review["quote"])}</p>'
            f'<p>{escape(bullet_review["assessment"])}</p>'
            f'<p class="job-alignment {escape(bullet_review["job_alignment"])}"><b>Target-job alignment</b>'
            f'{escape(bullet_review["job_alignment"].replace("-", " "))}: {escape(bullet_review["job_feedback"])}</p>'
            f'<div class="bullet-detail"><b>What works</b><ul>{strengths_list}</ul></div>{gaps_html}'
            f'<div class="suggestion"><b>Suggested bullet</b><p>{escape(bullet_review["suggestion"])}</p></div>'
            "</article>"
        )

    job_cards: list[str] = []
    for index, requirement in enumerate(requirements, 1):
        evidence = "".join(f"<li>{escape(item)}</li>" for item in requirement["evidence_quotes"])
        evidence_html = (
            f'<div class="job-evidence"><b>Resume evidence</b><ul>{evidence}</ul></div>'
            if evidence else '<p class="job-gap-note">No evidence found in this resume.</p>'
        )
        job_cards.append(
            f'<article class="job-match {escape(requirement["status"])}" id="job-note-{index}" tabindex="0">'
            f'<div class="job-match-meta"><span class="review-tag {escape(requirement["status"])}">J{index}</span><strong>{escape(requirement["status"].replace("-", " "))}</strong>'
            f'<small>{escape(requirement["priority"])}</small></div>'
            f'<h3>{escape(requirement["requirement"])}</h3>{evidence_html}'
            f'<p>{escape(requirement["feedback"])}</p></article>'
        )

    counts = {severity: sum(item["severity"] == severity for item in findings) for severity in SEVERITIES}
    match_counts = {status: sum(item["status"] == status for item in requirements) for status in JOB_MATCH_STATUSES}
    strengths_html = "".join(f"<li>{escape(item)}</li>" for item in strengths)
    unmatched_notice = (
        f'<p class="anchor-warning">{len(unmatched)} annotation anchor(s) were not found in the resume.</p>'
        if unmatched else ""
    )
    job_source = (
        f'<a href="{escape(target_job["source"], quote=True)}" rel="noopener noreferrer">View job posting</a>'
        if target_job["source"].startswith(("https://", "http://"))
        else escape(target_job["source"])
    )
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(candidate)} | Resume Review</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;700;800&display=swap');
:root{{--ink:#202520;--muted:#667068;--paper:#fff;--canvas:#edf0ec;--line:#d7ddd7;--accent:#244a3b;--green:#356b58;--green-soft:#eaf3ee;--amber:#8a5b12;--amber-soft:#fbf2df;--red:#a33a33;--red-soft:#faecea;--blue:#315f76;--blue-soft:#eaf2f6}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--canvas);color:var(--ink);font:14px/1.5 'DM Sans',sans-serif}}
button{{font:inherit}} .review-header{{background:#19382d;color:#f7faf7;padding:28px max(24px,calc((100vw - 1420px)/2));display:grid;grid-template-columns:minmax(0,1fr) auto;gap:28px;align-items:end}}
.kicker{{margin:0 0 6px;color:#b9cdbf;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.4px}} .review-header h1{{font:800 30px/1.15 Manrope,sans-serif;margin:0}}
.overall{{max-width:760px;margin:9px 0 0;color:#dce7df}} .counts{{display:flex;gap:8px;flex-wrap:wrap}} .counts span{{border:1px solid #ffffff35;padding:7px 10px;border-radius:6px;font-size:12px}}
.workspace{{max-width:1420px;margin:24px auto;display:grid;grid-template-columns:minmax(540px,816px) minmax(320px,1fr);gap:24px;padding:0 20px;align-items:start}}
.resume{{background:var(--paper);min-height:1056px;padding:52px 60px;box-shadow:0 10px 34px #24322912}} .resume-block{{position:relative}}
.resume h1{{font:800 34px/1.15 Manrope,sans-serif;margin:0 0 12px}} .resume h2{{font:700 11px/1.2 Manrope,sans-serif;text-transform:uppercase;letter-spacing:1.2px;color:var(--accent);border-bottom:1px solid var(--line);padding-bottom:6px;margin:24px 0 12px}}
.resume h3{{font:700 14px/1.35 Manrope,sans-serif;margin:14px 0 5px}} .resume p{{margin:0 0 9px}} .resume li{{margin:0 0 7px;padding-left:5px}}
.resume li::marker{{color:#7a847d}} mark{{background:var(--amber-soft);color:inherit;padding:1px 0}}
.annotated{{outline:1px solid #d8b56f;outline-offset:5px;border-radius:2px;background:#fffdf8}} .resume-block.selected{{outline:2px solid var(--blue);outline-offset:5px;border-radius:2px;background:var(--blue-soft)}}
.bullet-reviewed{{padding-left:8px}} .bullet-strong{{background:linear-gradient(90deg,var(--green-soft),transparent 38%)}} .bullet-needs-work{{background:linear-gradient(90deg,var(--amber-soft),transparent 38%)}}
.badges{{position:absolute;right:-48px;top:0;display:flex;gap:3px}} .badges button{{min-width:25px;height:25px;border:1px solid transparent;border-radius:13px;font-size:10px;font-weight:700;cursor:pointer;padding:0 6px}} .badges .finding-badge.critical{{background:var(--red-soft);border-color:#ddb5b1;color:var(--red)}} .badges .finding-badge.important,.badges .finding-badge.polish,.badges .bullet-badge.needs-work{{background:var(--amber-soft);border-color:#dfc48b;color:var(--amber)}} .badges .bullet-badge.strong{{background:var(--green-soft);border-color:#b8d1c5;color:var(--green)}} .badges .job-badge{{background:var(--blue-soft);border-color:#b8ccd6;color:var(--blue)}}
.review-panel{{position:sticky;top:16px;max-height:calc(100vh - 32px);overflow:auto;padding-right:6px}} .strengths{{padding:2px 2px 18px;border-bottom:1px solid var(--line);margin-bottom:18px}} .strengths h2{{font:700 15px Manrope,sans-serif;margin:0 0 6px}} .strengths ul{{margin:0;padding-left:18px;color:#4f5952}}
.anchor-warning,.unmatched{{color:var(--red);font-weight:700}} .annotation{{background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:18px 18px 17px;margin:0 0 12px;box-shadow:0 2px 10px #2432290a;scroll-margin-top:16px}}
.annotation.selected{{border-color:var(--blue);box-shadow:0 0 0 2px var(--blue-soft),0 8px 24px #24322914}}
.annotation-meta{{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:11px;text-transform:uppercase}} .annotation-meta span,.review-tag{{display:grid;place-items:center;min-width:25px;height:25px;padding:0 5px;border:1px solid transparent;border-radius:13px;font-weight:700}} .annotation.critical .annotation-meta span{{background:var(--red-soft);border-color:#ddb5b1;color:var(--red)}} .annotation.important .annotation-meta span,.annotation.polish .annotation-meta span{{background:var(--amber-soft);border-color:#dfc48b;color:var(--amber)}} .annotation-meta small{{margin-left:auto}}
.annotation-meta strong,.bullet-review-meta strong,.job-match-meta strong{{border-radius:4px;padding:3px 6px}} .annotation.critical .annotation-meta strong{{background:var(--red-soft);color:var(--red)}} .annotation.important .annotation-meta strong,.annotation.polish .annotation-meta strong{{background:var(--amber-soft);color:var(--amber)}}
.annotation h3{{font:700 16px/1.3 Manrope,sans-serif;margin:10px 0 7px}} .annotation p{{margin:0 0 10px}} .why b,.suggestion b{{display:block;font-size:11px;text-transform:uppercase;color:var(--muted);margin-bottom:3px}}
.suggestion{{background:#f1f5f1;padding:11px 12px;border-radius:6px}} .suggestion p{{margin:0}}
.panel-heading{{font:700 16px Manrope,sans-serif;margin:24px 0 10px}} .bullet-review{{background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:16px 18px;margin:0 0 10px;box-shadow:0 2px 10px #2432290a;scroll-margin-top:16px}} .bullet-review.selected{{border-color:var(--blue);box-shadow:0 0 0 2px var(--blue-soft),0 8px 24px #24322914}}
.bullet-review-meta{{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:11px;text-transform:uppercase}} .bullet-review-meta small{{margin-left:auto}} .bullet-review-meta .review-tag.strong{{background:var(--green-soft);border-color:#b8d1c5;color:var(--green)}} .bullet-review-meta .review-tag.needs-work{{background:var(--amber-soft);border-color:#dfc48b;color:var(--amber)}} .bullet-quote{{font-weight:600;margin:10px 0 8px}} .bullet-detail{{margin:10px 0}} .bullet-detail b{{display:block;font-size:11px;text-transform:uppercase;color:var(--muted)}} .bullet-detail ul{{margin:4px 0 0;padding-left:18px}} .bullet-detail.gaps{{color:#775219}}
.bullet-review.strong .bullet-review-meta strong{{background:var(--green-soft);color:var(--green)}} .bullet-review.needs-work .bullet-review-meta strong{{background:var(--amber-soft);color:var(--amber)}}
.target-job{{border-bottom:1px solid var(--line);padding-bottom:18px;margin-bottom:18px}} .target-job-heading{{display:flex;align-items:start;justify-content:space-between;gap:12px}} .target-job h2{{font:700 17px Manrope,sans-serif;margin:0 0 4px}} .target-job>p{{margin:0 0 9px;color:#4f5952}} .target-job .job-source{{font-size:12px}} .target-job a{{color:#315f76;font-weight:600}} .change-job{{border:1px solid #b8ccd6;background:var(--blue-soft);color:var(--blue);border-radius:5px;padding:6px 9px;font-size:12px;font-weight:700;white-space:nowrap;cursor:pointer}} .match-counts{{display:flex;gap:6px;flex-wrap:wrap;font-size:11px}} .match-counts span{{background:#fff;padding:5px 8px;border-radius:5px;border:1px solid var(--line)}}
.job-dialog{{width:min(560px,calc(100vw - 28px));border:1px solid var(--line);border-radius:6px;padding:0;box-shadow:0 24px 70px #13261e40;color:var(--ink)}} .job-dialog::backdrop{{background:#14251e99}} .job-dialog form{{padding:22px}} .job-dialog h2{{font:700 19px Manrope,sans-serif;margin:0 0 6px}} .job-dialog p{{margin:0 0 14px;color:#4f5952}} .job-dialog label{{display:block;font-size:12px;font-weight:700;margin-bottom:6px}} .job-dialog textarea{{display:block;width:100%;min-height:180px;resize:vertical;border:1px solid #bfc8c1;border-radius:5px;padding:10px 11px;font:13px/1.45 'DM Sans',sans-serif;color:var(--ink)}} .job-dialog textarea:focus{{outline:2px solid var(--blue-soft);border-color:var(--blue)}} .dialog-actions{{display:flex;justify-content:flex-end;gap:8px;margin-top:14px}} .dialog-actions button{{border:1px solid var(--line);border-radius:5px;padding:8px 11px;background:#fff;cursor:pointer;font-weight:700}} .dialog-actions .submit-job{{background:var(--accent);border-color:var(--accent);color:#fff}} .job-update-status{{min-height:21px;margin-top:10px!important;font-size:12px;font-weight:600}} .job-update-status.error{{color:var(--red)}} .job-update-status.success{{color:var(--green)}}
.job-match{{background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:16px 18px;margin:0 0 10px;box-shadow:0 2px 10px #2432290a;scroll-margin-top:16px}} .job-match.selected{{border-color:var(--blue);box-shadow:0 0 0 2px var(--blue-soft),0 8px 24px #24322914}} .job-match-meta{{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:11px;text-transform:uppercase}} .job-match-meta .review-tag{{background:var(--blue-soft);border-color:#b8ccd6;color:var(--blue)}} .job-match-meta small{{margin-left:auto}} .job-match.strong-match .job-match-meta strong{{background:var(--green-soft);color:var(--green)}} .job-match.partial-match .job-match-meta strong{{background:var(--amber-soft);color:var(--amber)}} .job-match.gap .job-match-meta strong{{background:var(--red-soft);color:var(--red)}} .job-match h3{{font:700 15px/1.35 Manrope,sans-serif;margin:9px 0 7px}} .job-evidence b,.job-alignment b{{display:block;font-size:11px;text-transform:uppercase;color:var(--muted)}} .job-evidence ul{{margin:4px 0 8px;padding-left:18px}} .job-gap-note{{font-weight:600;color:var(--red)}} .job-alignment{{background:var(--green-soft);padding:9px 10px;border-radius:5px}} .job-alignment.partial-match{{background:var(--amber-soft)}} .job-alignment.not-relevant{{background:#f1f2f1;color:#5f6761}}
@media(max-width:900px){{.review-header{{grid-template-columns:1fr}}.workspace{{grid-template-columns:1fr}}.review-panel{{position:static;max-height:none}}.resume{{min-height:0;padding:38px 42px}}}}
@media(max-width:560px){{.workspace{{padding:0 10px}}.resume{{padding:30px 36px 30px 24px}}.badges{{right:-30px}}.review-header{{padding:24px}}}}
</style></head><body>
<header class="review-header"><div><p class="kicker">Resume review · Target: {escape(target_job['title'])} at {escape(target_job['company'])}</p><h1>{escape(candidate)}</h1><p class="overall">{escape(overall)}</p></div>
<div class="counts"><span>{counts['critical']} critical</span><span>{counts['important']} important</span><span>{counts['polish']} polish</span></div></header>
<main class="workspace"><article class="resume" aria-label="Annotated resume">{''.join(document_parts)}</article>
<aside class="review-panel" aria-label="Review annotations"><section class="target-job"><div class="target-job-heading"><h2>{escape(target_job['title'])} · {escape(target_job['company'])}</h2><button type="button" class="change-job" id="change-job">Change job</button></div><p>{escape(target_job['summary'])}</p><p class="job-source">Source: {job_source}</p><div class="match-counts"><span>{match_counts['strong-match']} strong</span><span>{match_counts['partial-match']} partial</span><span>{match_counts['gap']} gaps</span></div></section><h2 class="panel-heading">Job requirement match</h2>{''.join(job_cards)}<section class="strengths"><h2>What already works</h2><ul>{strengths_html}</ul>{unmatched_notice}</section>{''.join(cards)}<h2 class="panel-heading">Bullet-by-bullet content review</h2>{''.join(bullet_cards)}</aside></main>
<dialog class="job-dialog" id="job-dialog"><form id="job-update-form"><h2>Change target job</h2><p>Enter a public job-posting URL or paste the full job description. Copilot will use it to regenerate this review.</p><label for="job-input">Job posting URL or description</label><textarea id="job-input" name="job" required placeholder="https://company.com/jobs/... or paste the full job description"></textarea><p class="job-update-status" id="job-update-status" role="status"></p><div class="dialog-actions"><button type="button" id="cancel-job">Cancel</button><button type="submit" class="submit-job">Save update request</button></div></form></dialog>
<script>
function selectNote(id){{document.querySelectorAll('.selected').forEach(el=>el.classList.remove('selected'));const note=document.getElementById(id);const target=document.querySelector(`[data-notes~="${{id}}"]`);note?.classList.add('selected');target?.classList.add('selected');note?.scrollIntoView({{behavior:'smooth',block:'nearest'}})}}
function selectBulletNote(id){{document.querySelectorAll('.selected').forEach(el=>el.classList.remove('selected'));const note=document.getElementById(id);const target=document.querySelector(`[data-bullet-review="${{id}}"]`);note?.classList.add('selected');target?.classList.add('selected');note?.scrollIntoView({{behavior:'smooth',block:'nearest'}})}}
function selectJobNote(id){{document.querySelectorAll('.selected').forEach(el=>el.classList.remove('selected'));const note=document.getElementById(id);const targets=[...document.querySelectorAll(`[data-job-matches~="${{id}}"]`)];note?.classList.add('selected');targets.forEach(target=>target.classList.add('selected'));note?.scrollIntoView({{behavior:'smooth',block:'nearest'}})}}
document.querySelectorAll('[data-note]').forEach(button=>button.addEventListener('click',()=>selectNote(button.dataset.note)));
document.querySelectorAll('[data-bullet-note]').forEach(button=>button.addEventListener('click',()=>selectBulletNote(button.dataset.bulletNote)));
document.querySelectorAll('[data-job-note]').forEach(button=>button.addEventListener('click',()=>selectJobNote(button.dataset.jobNote)));
document.querySelectorAll('.annotation').forEach(note=>note.addEventListener('click',()=>{{selectNote(note.id);document.querySelector(`[data-notes~="${{note.id}}"]`)?.scrollIntoView({{behavior:'smooth',block:'center'}})}}));
document.querySelectorAll('.bullet-review').forEach(note=>note.addEventListener('click',()=>{{selectBulletNote(note.id);document.querySelector(`[data-bullet-review="${{note.id}}"]`)?.scrollIntoView({{behavior:'smooth',block:'center'}})}}));
document.querySelectorAll('.job-match').forEach(note=>note.addEventListener('click',()=>{{selectJobNote(note.id);document.querySelector(`[data-job-matches~="${{note.id}}"]`)?.scrollIntoView({{behavior:'smooth',block:'center'}})}}));
const jobDialog=document.getElementById('job-dialog');const jobForm=document.getElementById('job-update-form');const jobInput=document.getElementById('job-input');const jobStatus=document.getElementById('job-update-status');
document.getElementById('change-job').addEventListener('click',()=>{{jobStatus.textContent='';jobStatus.className='job-update-status';jobDialog.showModal();jobInput.focus()}});
document.getElementById('cancel-job').addEventListener('click',()=>jobDialog.close());
jobForm.addEventListener('submit',async event=>{{event.preventDefault();const submit=jobForm.querySelector('[type="submit"]');submit.disabled=true;jobStatus.textContent='Saving update request...';jobStatus.className='job-update-status';try{{const token=document.querySelector('meta[name="review-update-token"]')?.content;if(!token)throw new Error('Open this review through its local preview server to update the job.');const response=await fetch('/update-job',{{method:'POST',headers:{{'Content-Type':'application/json','X-Review-Token':token}},body:JSON.stringify({{source:jobInput.value}})}});const result=await response.json();if(!response.ok)throw new Error(result.error||'Could not save the job update.');jobStatus.textContent='Saved. Return to Copilot Chat and say: Apply the job update from the preview.';jobStatus.className='job-update-status success'}}catch(error){{jobStatus.textContent=error.message;jobStatus.className='job-update-status error'}}finally{{submit.disabled=false}}}});
</script></body></html>'''
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def create_server(path: Path, resume_path: Path, review_path: Path, port: int = 0) -> ThreadingHTTPServer:
    path = path.resolve()
    resume_path = resume_path.resolve()
    review_path = review_path.resolve()
    request_path = path.with_name(f"{path.stem}_Job_Update.json")
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def respond(self, code: int, content: bytes, content_type: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self) -> None:
            if self.path not in ("/", f"/{path.name}"):
                self.respond(404, b"Not found", "text/plain")
                return
            html = path.read_text(encoding="utf-8").replace(
                "</head>", f'<meta name="review-update-token" content="{token}"></head>'
            )
            self.respond(200, html.encode("utf-8"), "text/html; charset=utf-8")

        def do_POST(self) -> None:
            if self.path != "/update-job":
                self.respond(404, b'{"error":"Not found"}', "application/json")
                return
            origin = f"http://127.0.0.1:{self.server.server_port}"
            if self.headers.get("Origin") != origin or self.headers.get("X-Review-Token") != token:
                self.respond(403, b'{"error":"Open the local review preview before updating."}', "application/json")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 131072:
                    raise ValueError("Invalid job description size")
                data = json.loads(self.rfile.read(length))
                source = data["source"].strip()
                parsed = urlparse(source)
                if parsed.scheme in ("http", "https") and parsed.netloc:
                    source_type = "url"
                elif len(source) >= 50:
                    source_type = "description"
                else:
                    raise ValueError("Paste the full job description or enter a valid public URL")
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
                content = json.dumps({"error": str(error)}).encode("utf-8")
                self.respond(400, content, "application/json")
                return
            request_path.write_text(json.dumps({
                "status": "pending",
                "resume": str(resume_path),
                "review": str(review_path),
                "source_type": source_type,
                "source": source,
            }, indent=2), encoding="utf-8")
            content = json.dumps({"status": "saved", "request_file": request_path.name}).encode("utf-8")
            self.respond(200, content, "application/json")

        def log_message(self, format: str, *args) -> None:
            return

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(path: Path, resume_path: Path, review_path: Path, port: int) -> None:
    server = create_server(path, resume_path, review_path, port)
    print(f"Resume review: http://127.0.0.1:{server.server_port}/{path.name}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("resume", type=Path)
    parser.add_argument("review", type=Path, nargs="?", help="Structured review JSON")
    parser.add_argument("--extract", action="store_true", help="Print visible resume blocks as JSON")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    if args.extract:
        try:
            blocks = extract_blocks(args.resume)
        except (OSError, ValueError) as error:
            print(f"Error: {error}", file=sys.stderr)
            return 2
        print(json.dumps([block.__dict__ for block in blocks], indent=2, ensure_ascii=False))
        return 0
    if args.review is None:
        parser.error("review JSON is required unless --extract is used")
    output = args.output or Path("output/reviews") / f"{args.resume.stem}_Review.html"
    try:
        result = build_html(args.resume, args.review, output.resolve())
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    if args.serve:
        serve(result, args.resume, args.review, args.port)
    else:
        print(f"Resume review saved to: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())