---
name: ats-resume-checker
description: Checks Markdown and Word resumes for ATS parsing risks, standard section structure, portfolio visibility, and recruiter scanability. Use when reviewing ATS compatibility, validating a resume before applying, comparing resume layouts, or diagnosing why a .docx may parse poorly.
---

# ATS Resume Checker

## Purpose

Evaluate whether a resume is likely to preserve its reading order and key information in common applicant tracking systems. Treat the score as a structural risk estimate, not a guarantee from any specific ATS vendor.

## Workflow

1. Identify the resume file to check. Prefer the final `.docx`; use `.md` for an early content check.
2. Run:

   ```bash
   python3 .github/skills/ats-resume-checker/scripts/check_ats.py <resume-file>
   ```

3. Review findings in this order:
   - **Critical:** likely reading-order or content-loss risk
   - **High:** important recruiter or parser failure
   - **Medium:** inconsistent parsing or discoverability risk
   - **Low:** polish and convention issue
4. Fix critical and high findings first.
5. Regenerate the `.docx` and rerun the checker. Do not claim improved compatibility until the executable check confirms it.
6. For a final application, also paste the resume into a plain-text editor and confirm that name, contact details, experience, education, and skills appear in the intended order.

## Compatibility Bands

- **90-100, High:** simple structure with standard headings and visible contact links
- **75-89, Moderate:** generally parseable with one or more meaningful risks
- **0-74, Low:** substantial reading-order, extraction, or discoverability risks

## High-Compatibility Layout

- Use one column and normal paragraphs.
- Keep name and contact details in the document body, not headers, footers, text boxes, or shapes.
- Put a complete portfolio URL first in the contact line.
- Use standard headings: Summary, Experience, Projects, Education, Skills, Tools.
- Use plain bullets and reverse-chronological experience.
- Avoid tables, sidebars, icons, photos, charts, and manually drawn separators.
- Keep the filename descriptive: `FirstName_LastName_ProductDesigner_Resume.docx`.
- Preserve a separate designed version only for direct recruiter outreach or portfolio downloads.

## Output Requirements

Report:

1. Compatibility score and band
2. Findings ordered by severity
3. Why each issue affects parsing or recruiter scanning
4. A concrete fix for each issue
5. A short verdict: safe for ATS upload, revise before upload, or use only for direct sharing

Do not imply that any automated checker can certify compatibility with every ATS.
