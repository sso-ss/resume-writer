---
name: resume-writing
description: "Writes and tailors Product Designer resumes. Use when creating, rewriting, tailoring to a job posting, or converting resume content to Word, PDF, or editable HTML."
---

# Product Designer Resume Writing

Start by pasting career information or saying “help me write a resume” to begin the interview.

## When to Use
- User wants to create a new Product Designer resume from scratch
- User wants to rewrite or improve an existing resume
- User has a job posting URL and wants a tailored resume
- User wants to convert resume content to .docx format

## Writing Principle

Make the candidate's fit clear, then support it with relevant, credible evidence. Follow the candidate's actual experience and target role; section counts and word counts are defaults, not quotas.

## Two Workflow Paths

### Path A: Interview Mode
When career details are missing, ask in small batches, skipping information already supplied:

1. **Target:** Role, level, product/domain, and an optional job posting. Gather these early so achievement selection reflects the opening.
2. **Background:** Actual titles, employers, dates, relevant experience, education, and portfolio/contact details.
3. **Evidence:** For the strongest relevant work, establish the problem, personal ownership versus team contribution, key decision or constraint, result, and how the result was evaluated. Ask follow-ups only when missing evidence would materially improve the resume.
4. **Skills:** Design, research, collaboration and leadership capabilities, plus tools the candidate can discuss confidently.
5. **AI:** Where have you used AI in your design process or designed an AI feature, and how did you validate the result? Distinguish workflow assistance, AI product design, and evaluation/judgment. Do not assume AI experience.
6. **Additional evidence:** Ask about independent, academic, or portfolio projects only when they add relevant evidence missing from employment. Gather meaningful recognition without an award-count minimum.
7. **Layout:** Offer `single-column` (default), `two-column-left`, `two-column-right`, `two-column-right-refined`, or `editorial-html`. Preserve an existing choice.

### Path B: Paste-and-Go
Parse the supplied career information first. Establish the target and strongest evidence, then ask only for critical missing details or clarifications that affect accuracy or relevance. Do not repeat the full interview. Use the selected layout, or default to single-column if there is no preference.

For critique of an uploaded resume, use the separate `resume-review` skill. Return here when the user approves revisions or asks for a rewrite. The writing quality checks below also apply during generation; they do not require a separate review workflow.

## Resume Generation Procedure

### Step 1: Load Guidelines
Read [recruiter-guidelines.md](./references/recruiter-guidelines.md) for section selection, evidence standards, AI treatment, seniority, and the two review perspectives.

### Step 2: Assess Scope and Career Context
Assess seniority using demonstrated ownership, autonomy, complexity, influence, and sustained impact. Years and titles provide context, not automatic level thresholds. Preserve actual employment titles; do not promote the candidate to match a posting. Distinguish senior individual contributors from people managers.

Choose section emphasis from the whole career. Recent graduation, a bootcamp, or a career change alone does not make someone a new graduate. Lead with the strongest relevant evidence: professional work, transferable experience, or projects and education. Clarify only when that choice is materially uncertain.

### Step 3: Write Content (Markdown)

**Experienced-designer default:**
- Name + Contact, with a prominent portfolio URL
- Summary when it adds useful positioning: two concise sentences, roughly 30–50 words, combining identity/specialization with one relevant career achievement
- Experience, reverse chronological, with most space for relevant ownership, decisions, and results
- Skills & Tools, compact; Education, brief (sidebar layouts may position these differently)
- Projects and Recognition only when they add meaningful evidence; omit empty sections

**Projects are conditional:** Omit Key/Selected Projects when it repeats Experience. Place useful case-study links beside the corresponding work. Include a separate section when academic, independent, or other projects demonstrate capabilities missing from employment. For early-career candidates, projects and education may lead, but substantive internships or transferable work can be stronger evidence.

**Summary selection:** Choose the achievement most relevant to the target role, not automatically the largest number or latest project. Include leadership or AI when central to that fit and supported. Do not crowd the summary with a generic soft-skills list. A specific qualitative achievement is valid when metrics are unavailable. If no posting is supplied, use the stated target; do not invent employer requirements.

**Skills:** Default to Design, Research, and Collaboration & Leadership, generally 3–4 relevant items each, plus a short tools line. Keep soft skills visible and substantiate important ones in Experience. Add a concise AI line only for supported, relevant capabilities. Counts are flexible; never fill a category with invented skills.

For fictional demos, clearly identify the example as fictional in accompanying documentation and use fictional company/product names and reserved example URLs. Preserve real employers and facts when working from actual candidate experience. Never transfer demo claims into a real resume.

**Readable typography:** Use 10.5 pt body text by default and a minimum of 9 pt for all visible resume text, including summaries, sidebar content, dates, contact details, and section labels. Reserve 9 pt for secondary details when needed; retain 10.5 pt body text where practical. Specify print sizes in points; 9 pt equals 12 px. Apply the same minimum to HTML previews, Word, and PDF. Fill a page with relevant evidence and balanced spacing, never filler or smaller type. If the content does not fit, edit repetition, adjust reasonable spacing, or allow another page. Verify actual export pagination and font sizes.

### Step 4: Tailor to the Target (if applicable)
For a supplied posting URL or pasted description, identify the main requirements, choose the summary achievement accordingly, and front-load relevant bullets within each role. Use the posting's terminology only where supported by the candidate's evidence. Preserve actual titles, scope, and attribution. If a URL cannot be read, request pasted text rather than inventing requirements.

### Step 5: Save as Markdown
Save the resume as `{FirstName}_{LastName}_Resume.md` in the workspace.

### Step 6: Generate the editable HTML review first
Use the shared preview template's default app style: white and light-gray surfaces, black sans-serif interface text, clear action buttons, and restrained lime accents. Keep interface controls independent of the resume accent picker. Static labels should not look like buttons. Apply this interface consistently across all five resume layouts; the selected document layout controls the resume and its exports.

Start `python3 .github/skills/resume-writing/scripts/serve_resume.py {FirstName}_{LastName}_Resume.md --layout {selected-layout}` as a long-running local server, then open and link the localhost URL. The first user-facing artifact must be this editable HTML preview, initially using the layout the user selected. The Template menu lets the user compare all five layouts without losing browser edits. Do not pre-generate or present Word/PDF as final before review. Keep the server running while the user reviews and downloads. **Save as Word** and **Save as PDF** use the currently selected layout and include browser edits. Word needs the layout fonts installed for the closest match; line wrapping can vary by renderer. A standalone `file://` HTML cannot run Python exports. Browser edits do not update the source Markdown; incorporate approved changes there when they should become source content. ATS checking is separate from the preview; run it on the exported Word file when requested. Do not claim a one-page export without checking the actual file.

For editorial Word typography, install DM Sans and the static Manrope ExtraBold face, then restart Word if it was open during installation. Verify the actual Word render; Quick Look may substitute fonts or ignore tab alignment. Editorial Word exports use `build_layout_editorial`, never the refined-right generator.

#### PDF Downloads
**Save as PDF** uses the local server's Playwright Chromium renderer to download a text-based PDF with browser edits. Do not use the integrated browser's print dialog, which can produce an image-only PDF. Install these dependencies in the same Python environment as the server:
```sh
python3 -m pip install -r .github/skills/resume-writing/requirements-pdf.txt
python3 -m playwright install chromium
```
Check the actual PDF's extractable text and page count before delivery. Selectable text does not guarantee ATS compatibility.

### Step 6.1: Export after preview approval
Before running any script, check dependencies silently:
- `python3 --version` — if this fails, tell the user: "Python 3 is required for .docx export. Download it from https://python.org (check 'Add to PATH' during install), then try again."
- `python3 -c "import docx"` — if this fails, run `pip3 install python-docx` automatically

Use the preview's export buttons after approval. For non-interactive regeneration, run the conversion script based on structure choice:
- Single-column: [to_docx.py](./scripts/to_docx.py)
- Two-column-left (Layout B): [to_docx_two_column.py](./scripts/to_docx_two_column.py)
- Two-column-right (Layout C): [to_docx_right_sidebar.py](./scripts/to_docx_right_sidebar.py)
- Two-column-right-refined: [to_docx_right_sidebar_refined.py](./scripts/to_docx_right_sidebar_refined.py)
- Editorial HTML preview: [to_html_editorial.py](./scripts/to_html_editorial.py)
- Editorial Word: [to_docx_editorial.py](./scripts/to_docx_editorial.py)

Usage:
- `python3 .github/skills/resume-writing/scripts/to_docx.py {FirstName}_{LastName}_Resume.md`
- `python3 .github/skills/resume-writing/scripts/to_docx_two_column.py {FirstName}_{LastName}_Resume.md`
- `python3 .github/skills/resume-writing/scripts/to_docx_right_sidebar.py {FirstName}_{LastName}_Resume.md`
- `python3 .github/skills/resume-writing/scripts/to_docx_right_sidebar_refined.py {FirstName}_{LastName}_Resume.md`
- `python3 .github/skills/resume-writing/scripts/to_html_editorial.py {FirstName}_{LastName}_Resume.md`
- `python3 .github/skills/resume-writing/scripts/to_docx_editorial.py {FirstName}_{LastName}_Resume.md`

The refined layout produces `{FirstName}_{LastName}_ProductDesigner_Resume_RightRefined.docx`; the editorial scripts produce `{FirstName}_{LastName}_ProductDesigner_Resume_Editorial.html` and `{FirstName}_{LastName}_ProductDesigner_Resume_Editorial.docx`; the other layouts produce `{FirstName}_{LastName}_ProductDesigner_Resume.docx` in the same directory. When generating multiple layouts together, pass a distinct output path as the second script argument for each so files do not overwrite each other.

### Step 6.2: ATS Warning (required for two-column)
If the user selects `two-column-left`, `two-column-right`, `two-column-right-refined`, or `editorial-html`, explicitly warn:
- Some ATS systems parse two-column resumes less reliably
- Recommend keeping a single-column version for applications
- Suggest using two-column version mainly for networking, direct recruiter outreach, or portfolio downloads
- For `editorial-html`, use the editable preview's PDF or Word download for direct sharing; keep the single-column Word version for ATS uploads.

### Step 7: Review from Both Perspectives
Before delivery, apply both passes from the recruiter guidelines:
- **Recruiter:** Clear role fit, readable chronology, relevant achievement, appropriate level, and accessible portfolio/contact information.
- **Hiring manager:** Personal ownership, design judgment, craft, constraints, collaboration, and credible impact. AI claims describe actual use and validation when relevant.

Remove repetition and unsupported claims. Ask the user to resolve remaining factual uncertainty; do not fill gaps with invented numbers, responsibilities, skills, or outcomes. Invite corrections to positioning and accuracy without repeating questions already answered.

## Evidence and Bullet Examples

Use XYZ (accomplishment, measurement, method) when it naturally fits verified evidence. Other useful structures include problem → decision → consequence, or ownership → action → concrete result. A number is not required in every bullet. Across the selected bullets, make ownership, judgment, and outcomes clear without packing every dimension into every sentence.

Illustrative examples, to use only when the underlying facts are supplied:
- Redesigned merchant dashboard navigation based on card-sort findings, reducing time-to-insight by 40%.
- Resolved a conflict between finance and support workflows by separating account-level permissions from transaction-level actions; the revised model shipped in the admin portal.
- Used Claude to explore interaction prototypes, then evaluated the alternatives in moderated usability sessions before selecting the onboarding flow.
- Tested a capstone prototype with eight participants; recurring navigation errors informed a revised information architecture. (Research scope and a design decision, not a claimed production outcome.)

Avoid generic responsibilities, unsupported causality, and tool lists presented as achievements. Keep measurement context where it matters: prototype testing versus production analytics, observed versus estimated results, and personal versus team contribution. Never invent an estimate or imply the entire platform audience used a feature.

## Output Quality Checklist
- [ ] Target fit is clear; actual titles and career context are preserved.
- [ ] Summary, if present, combines positioning with one relevant, supported achievement; roughly 30–50 words is a guideline.
- [ ] Experience shows specific contributions and meaningful evidence, with verified metrics where available.
- [ ] Important collaboration and leadership skills have supporting examples.
- [ ] AI claims, if present, reflect actual workflows/product work and validation; no generic expertise claims.
- [ ] Projects and recognition add evidence rather than repeat Experience; no empty headings.
- [ ] Skills are concise, relevant, defensible, and retain supported soft skills; tools are compact.
- [ ] Portfolio and case-study URLs are correctly formed; placeholders are identified before application use.
- [ ] Dates are consistent; strongest relevant work receives the most space.
- [ ] Aim for one readable page; allow two when relevant experience warrants it. Check actual export pagination, text extraction, and layout rather than shrinking text to force a page count.
- [ ] Body text defaults to 10.5 pt; all visible resume text is at least 9 pt in the preview and exports. Verify computed/rendered sizes rather than confusing CSS pixels with points.
- [ ] Both recruiter and hiring-manager passes are complete; remaining factual uncertainty is surfaced.
