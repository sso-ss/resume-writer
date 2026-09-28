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
        if "block_id" in finding:
            index = referenced_block(blocks, finding["block_id"], finding["quote"])
            matches.setdefault(index, []).append(finding_index)
            continue
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


def referenced_block(blocks: list[Block], identifier: str, quote: str) -> int:
    if not isinstance(identifier, str) or not re.fullmatch(r"r[1-9][0-9]*", identifier):
        raise ValueError("Invalid resume block ID")
    index = int(identifier[1:]) - 1
    if index >= len(blocks) or not quote or quote not in blocks[index].text:
        raise ValueError(f"Evidence does not match resume block {identifier}")
    return index


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
        if "block_id" in bullet_review:
            index = referenced_block(blocks, bullet_review["block_id"], bullet_review["quote"])
            if (index not in reviewable or index in matches
                    or blocks[index].text != bullet_review["quote"]
                    or normalize(blocks[index].section) != section):
                raise ValueError("Bullet ID must reference one complete, unreviewed Experience or Projects bullet")
            matches[index] = review_index
            continue
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
        if "evidence_ids" in requirement:
            if len(requirement["evidence_ids"]) != len(requirement["evidence_quotes"]):
                raise ValueError("Evidence IDs and quotes must have equal length")
            for identifier, quote in zip(requirement["evidence_ids"], requirement["evidence_quotes"]):
                index = referenced_block(blocks, identifier, quote)
                matches.setdefault(index, []).append(requirement_index)
            continue
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


def build_html(resume_path: Path, review_path: Path, output_path: Path, *, app_review_id: str = "") -> Path:
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
    feedback_heading = '<h2 class="panel-heading">Resume feedback</h2>' if findings else ""
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
    update_url = f"/api/reviews/{app_review_id}/job" if app_review_id else "/update-job"
    start_link = ('<nav class="review-nav"><a class="review-brand" href="/">Resume Review</a>'
                  '<a class="new-review" href="/">Review another resume ↗</a></nav>') if app_review_id else ""
    stylesheet = (Path(__file__).resolve().parent.parent / "templates/review-page.css").read_text(encoding="utf-8")
    job_dialog_description = ("Add the new posting to generate a fresh review of this resume."
                              if app_review_id else "Enter a public job-posting URL or paste the full job description. Your assistant will use it to regenerate this review.")
    job_submit_label = "Review this job" if app_review_id else "Save update request"
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(candidate)} | Resume Review</title>
<style>{stylesheet}</style></head><body>{start_link}
<header class="review-header"><div><p class="kicker">Resume review · Target: {escape(target_job['title'])} at {escape(target_job['company'])}</p><h1>{escape(candidate)}</h1><p class="overall">{escape(overall)}</p></div></header>
<section class="review-key" aria-label="Feedback filters and annotation key"><div class="review-key-heading"><strong>Explore your feedback</strong><span>Filter suggestions by severity</span></div><div class="severity-filters" role="group" aria-label="Filter suggestions by severity"><button type="button" data-severity-filter="all" aria-pressed="true">All suggestions <b>{len(findings)}</b></button><button type="button" data-severity-filter="critical" aria-pressed="false">Critical <b>{counts['critical']}</b></button><button type="button" data-severity-filter="important" aria-pressed="false">Important <b>{counts['important']}</b></button><button type="button" data-severity-filter="polish" aria-pressed="false">Polish <b>{counts['polish']}</b></button></div><div class="annotation-key" aria-label="Annotation key"><span><b class="key-job">J</b> Job requirement</span><span><b class="key-bullet">B</b> Bullet review</span><span><b>1</b> Suggested improvement</span></div><span id="filter-status" class="visually-hidden" role="status">Showing all suggestions.</span></section>
<main class="workspace"><article class="resume" aria-label="Annotated resume">{''.join(document_parts)}</article>
<aside class="review-panel" aria-label="Review annotations"><section class="target-job"><div class="target-job-heading"><h2>{escape(target_job['title'])} · {escape(target_job['company'])}</h2><button type="button" class="change-job" id="change-job">Change job</button></div><p>{escape(target_job['summary'])}</p><p class="job-source">Source: {job_source}</p><div class="match-counts" aria-label="Job requirement match summary"><span><b>{match_counts['strong-match']}</b> strong</span><span><b>{match_counts['partial-match']}</b> partial</span><span><b>{match_counts['gap']}</b> gaps</span></div></section><h2 class="panel-heading">Job requirement match</h2>{''.join(job_cards)}<section class="strengths"><h2>What already works</h2><ul>{strengths_html}</ul>{unmatched_notice}</section>{feedback_heading}{''.join(cards)}<h2 class="panel-heading">Bullet-by-bullet content review</h2>{''.join(bullet_cards)}</aside></main>
<dialog class="job-dialog" id="job-dialog"><form id="job-update-form"><h2>Change target job</h2><p>{job_dialog_description}</p><label for="job-input">Job posting URL or description</label><textarea id="job-input" name="job" required placeholder="https://company.com/jobs/... or paste the full job description"></textarea><p class="job-update-status" id="job-update-status" role="status"></p><div class="dialog-actions"><button type="button" id="cancel-job">Cancel</button><button type="submit" class="submit-job">{job_submit_label}</button></div></form></dialog>
<script>
function applySeverityFilter(severity){{let shown=0;document.querySelectorAll('.annotation').forEach(note=>{{const visible=severity==='all'||note.classList.contains(severity);note.hidden=!visible;if(visible)shown++}});document.querySelectorAll('.resume-block[data-notes]').forEach(block=>{{const badges=block.querySelectorAll('[data-note]');badges.forEach(badge=>{{badge.hidden=document.getElementById(badge.dataset.note)?.hidden||false}});block.classList.toggle('filtered-annotation',severity!=='all'&&![...badges].some(badge=>!badge.hidden))}});document.querySelectorAll('[data-severity-filter]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.severityFilter===severity)));const label=severity==='all'?'all':severity;document.getElementById('filter-status').textContent=`Showing ${{shown}} ${{label}} suggestions.`}}
document.querySelectorAll('[data-severity-filter]').forEach(button=>button.addEventListener('click',()=>applySeverityFilter(button.dataset.severityFilter)));
function selectNote(id){{const note=document.getElementById(id);if(note?.hidden)applySeverityFilter('all');document.querySelectorAll('.selected').forEach(el=>el.classList.remove('selected'));const target=document.querySelector(`[data-notes~="${{id}}"]`);note?.classList.add('selected');target?.classList.add('selected');note?.scrollIntoView({{behavior:'smooth',block:'nearest'}})}}
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
jobForm.addEventListener('submit',async event=>{{event.preventDefault();const submit=jobForm.querySelector('[type="submit"]');submit.disabled=true;jobStatus.textContent='Saving update request...';jobStatus.className='job-update-status';try{{const token=document.querySelector('meta[name="review-update-token"]')?.content;if(!token)throw new Error('Open this review through its local preview server to update the job.');const response=await fetch({json.dumps(update_url)},{{method:'POST',headers:{{'Content-Type':'application/json','X-Review-Token':token}},body:JSON.stringify({{source:jobInput.value}})}});const result=await response.json();if(!response.ok)throw new Error(result.error||'Could not save the job update.');if(result.redirect_url){{window.location.assign(result.redirect_url);return;}}jobStatus.textContent='Saved. Return to Copilot Chat and say: Apply the job update from the preview.';jobStatus.className='job-update-status success'}}catch(error){{jobStatus.textContent=error.message;jobStatus.className='job-update-status error'}}finally{{submit.disabled=false}}}});
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
    parser.add_argument("resume", type=Path, nargs="?")
    parser.add_argument("review", type=Path, nargs="?", help="Structured review JSON")
    parser.add_argument("--extract", action="store_true", help="Print visible resume blocks as JSON")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--provider", choices=("auto", "codex", "claude", "cursor", "copilot"), default="auto",
                        help="AI connection for the upload app; auto detects the launching terminal")
    parser.add_argument("--open", action="store_true", help="Open the upload screen in your browser")
    args = parser.parse_args()
    if args.resume is None:
        if args.extract or args.review or args.output:
            parser.error("a resume is required for extraction or rendering")
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from review_app import serve_app
        serve_app(port=args.port, provider=args.provider, open_browser=args.open)
        return 0
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
