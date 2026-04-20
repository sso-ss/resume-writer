---
name: resume-writing
description: "Write and tailor Product Designer resumes. Use when: creating a resume, rewriting a resume, tailoring a resume to a job posting, reviewing resume content, converting resume to .docx format."
argument-hint: "Paste your career info, or say 'help me write a resume' to start the interview"
---

# Product Designer Resume Writing

## When to Use
- User wants to create a new Product Designer resume from scratch
- User wants to rewrite or improve an existing resume
- User has a job posting URL and wants a tailored resume
- User wants to convert resume content to .docx format

## Three Workflow Paths

### Path A: Interview Mode
Triggered when the user says something vague like "help me write a resume" without providing career details.

Ask these questions in order (use structured questions when possible):

1. **Target role:** What specific Product Design role are you targeting? (e.g., Senior Product Designer, Staff Designer, UX Designer)
2. **Years of experience:** How many years of professional design experience do you have?
3. **Domain:** What industry/product type? (B2B SaaS, consumer mobile, e-commerce, marketplace, etc.)
4. **Contact info:** Full name, email, location (city, state or "Remote"), LinkedIn URL, portfolio URL
5. **Current/most recent role:** Company name, title, dates, and 4-5 key achievements with metrics
6. **Previous roles:** For each (up to 2-3 more): company, title, dates, 2-3 key achievements
7. **Key projects:** 2-3 standout projects you'd want a recruiter to click on (with case study links if available)
8. **Education:** Degree, university, graduation year, any notable honors
9. **Skills:** Your strongest design skills, research skills, and soft skills
10. **Tools:** Design and collaboration tools you use daily
11. **Job posting:** (Optional) Paste or link a job posting to tailor the resume
12. **Structure choice:** `single-column` (ATS-safe default), `two-column-left` (sidebar left, designer feel), or `two-column-right` (full-width header, F-pattern)

### Path B: Paste-and-Go
Triggered when the user provides raw career information (even if messy or unstructured).

1. Parse the provided information and identify all resume sections
2. Detect if new grad (see new-grad detection signals in Step 2 below)
3. Ask only for critical missing information (name, portfolio link, target role level)
4. Ask for structure choice: `single-column`, `two-column-left`, or `two-column-right`
5. Proceed directly to generating the resume

### Path C: Review Mode
Triggered when the user provides an existing resume and asks for review, feedback, or critique.

1. Parse the resume and identify all sections
2. Read the recruiter guidelines: [recruiter-guidelines.md](./references/recruiter-guidelines.md)
3. Evaluate each section against the Review Checklist (below)
4. Rate each section: **Strong** / **Needs Work** / **Critical Issue**
5. For every issue found, output:
   - **Section** — which section has the problem
   - **Issue** — what's wrong (one sentence)
   - **Why it matters** — recruiter impact (one sentence)
   - **Before** — the current text from the resume
   - **Suggested** — a rewritten version following XYZ formula and guidelines
6. After all issues, ask:
   > "Want me to generate a full rewrite with all these fixes applied?"
7. If user says yes, switch to Path B (paste-and-go) using the original resume content + review fixes

## Resume Generation Procedure

Follow these steps in order:

### Step 1: Load Guidelines
Read the recruiter guidelines: [recruiter-guidelines.md](./references/recruiter-guidelines.md)

### Step 2: Determine Seniority
Based on years of experience and role titles, determine the candidate's seniority level. This affects bullet language, section order, and focus:
- **New Grad / Student (0 years):** no professional roles or internship-only. Triggers new-grad mode (see below)
- Junior/Mid (0-3 years): craft execution, shipping, learning
- Senior (3-6 years): end-to-end ownership, research-driven decisions, design systems
- Staff/Principal (6+ years): cross-product strategy, practice building, org-level impact
- Lead/Manager: team building, culture, process, business outcomes

**New-grad detection signals** (any one triggers new-grad mode):
- Years of experience = 0
- Keywords: "student," "new grad," "graduating," "bootcamp," "career change"
- No professional design roles (only projects, coursework, volunteer)
- Only role is an internship
- Graduation date within last 12 months or in the future

When new-grad mode is detected, confirm with the user:
> "Based on your background, I'll structure this as an early-career resume — Education first, Projects as your main proof of capability. Sound right?"

### Step 3: Write Content (Markdown)
Generate the resume content in Markdown format following the guidelines strictly.

**Experienced designer (1+ years):**
- Name + Contact (portfolio link first)
- Summary (exactly 3 lines)
- Experience (XYZ formula bullets, varied structures, proper verb usage)
- Key Projects (2-3 with links)
- Recognition (optional — only if 3+ notable design awards)
- Education (1-2 lines)
- Skills (grouped) & Tools (single line)

**New grad / student (0 years):**
- Name + Contact (portfolio link first)
- Summary (3 lines, reframed: what you studied + strongest project outcome + differentiator)
- Education (moved up — primary credential, include relevant coursework)
- Projects (2-4 projects, 2-3 XYZ bullets each, link case studies)
- Experience (only if internships or relevant part-time exist — omit if none)
- Volunteer (only if design-related pro bono work — omit generic volunteering)
- Skills (grouped) & Tools (single line)

### Step 4: Job Posting Tailoring (if applicable)
If a job posting URL was provided:
1. Fetch the posting using web tools
2. Extract the top 5-7 requirements
3. Mirror exact keywords in bullets
4. Reorder bullets to front-load relevant work
5. Adjust Summary and Skills to match

### Step 5: Save as Markdown
Save the resume as `{FirstName}_{LastName}_Resume.md` in the workspace.

### Step 6: Convert to .docx
Before running any script, check dependencies silently:
- `python3 --version` — if this fails, tell the user: "Python 3 is required for .docx export. Download it from https://python.org (check 'Add to PATH' during install), then try again."
- `python3 -c "import docx"` — if this fails, run `pip3 install python-docx` automatically

Run the conversion script based on structure choice:
- Single-column: [to_docx.py](./scripts/to_docx.py)
- Two-column-left (Layout B): [to_docx_two_column.py](./scripts/to_docx_two_column.py)
- Two-column-right (Layout C): [to_docx_right_sidebar.py](./scripts/to_docx_right_sidebar.py)

Usage:
- `python3 .github/skills/resume-writing/scripts/to_docx.py {FirstName}_{LastName}_Resume.md`
- `python3 .github/skills/resume-writing/scripts/to_docx_two_column.py {FirstName}_{LastName}_Resume.md`
- `python3 .github/skills/resume-writing/scripts/to_docx_right_sidebar.py {FirstName}_{LastName}_Resume.md`

This produces `{FirstName}_{LastName}_ProductDesigner_Resume.docx` in the same directory.

### Step 6.1: ATS Warning (required for two-column)
If the user selects `two-column-left` or `two-column-right`, explicitly warn:
- Some ATS systems parse two-column resumes less reliably
- Recommend keeping a single-column version for applications
- Suggest using two-column version mainly for networking, direct recruiter outreach, or portfolio downloads

### Step 7: Review
Present the resume to the user and ask:
- Does the Summary accurately represent your identity and top achievement?
- Are there any bullets that overstate or misrepresent your experience?
- Is anything important missing?
- Would you like me to tailor this to a specific job posting?

## XYZ Formula Reference

Every experience bullet should follow: **Accomplished [X] as measured by [Y] by doing [Z]**

**Good examples for Product Designers:**
- Redesigned the onboarding flow for a B2B analytics platform, increasing user activation by 28% by simplifying the 12-step setup to 4 contextual steps
- Built a component library of 120+ components in Figma adopted by 4 product teams, reducing design-to-dev handoff time by 40%
- Conducted 30+ usability sessions that uncovered a critical navigation issue, leading to a restructured IA that reduced support tickets by 22%
- Led design for a 0→1 collaboration feature serving 50K+ users, driving a 15% increase in weekly active usage within 3 months of launch

**Good examples for New Grads / Students:**
- Redesigned a campus dining app navigation for a capstone project, reducing average task completion time by 40% across 8 moderated usability sessions
- Conducted 12 user interviews and synthesized findings into 3 persona archetypes, shifting the team's design direction from feature-based to goal-based navigation
- Designed and prototyped a budgeting tool during a 48-hour hackathon, earning 1st place among 30 teams by scoring highest on usability and visual polish criteria
- Built a 45-component UI kit in Figma for a student design collective, adopted by 6 project teams and reducing initial wireframing time by an estimated 50%

**Bad examples (do NOT generate these):**
- Designed user interfaces for various projects (no metric, no method)
- Collaborated with engineers to improve the product (vague, no outcome)
- Used Figma and AI tools to create wireframes (tool-focused, not impact-focused)
- [Achievement 1]: Led the redesign of the dashboard (labeled, template-like)

## Output Quality Checklist
Before delivering the final resume, verify:
- [ ] One page worth of content (not too dense, not too sparse)
- [ ] Portfolio link is the first contact item
- [ ] Summary is exactly 3 lines, no filler phrases
- [ ] Most recent role has 4-5 bullets, older roles have 2-3
- [ ] Every bullet starts with a strong action verb
- [ ] Every bullet has at least one metric/number
- [ ] No two roles have the same bullet structure
- [ ] Seniority language matches candidate's level
- [ ] Skills are grouped into 3 categories
- [ ] Tools are on a single line
- [ ] No personal pronouns (I, me, my)
- [ ] Date format is consistent (Mon YYYY – Mon YYYY)
- [ ] If tailored: job posting keywords appear naturally in bullets

## Review Checklist

Use this checklist when reviewing an existing resume (Path C). Check every item and flag failures.

### Structure
- [ ] Portfolio link is FIRST in contact info
- [ ] Portfolio is publicly accessible (no password)
- [ ] Summary is exactly 3 lines (identity + impact + differentiator)
- [ ] Section order matches recruiter-guidelines.md
- [ ] Content fits one page
- [ ] Key Projects section exists with case study links

### Content Quality
- [ ] Every bullet uses XYZ formula (Accomplished X, measured by Y, by doing Z)
- [ ] Every bullet starts with a strong action verb (past tense for past roles)
- [ ] Every bullet has at least one metric/number
- [ ] No filler phrases ("passionate about," "detail-oriented," "team player")
- [ ] No repeated bullet patterns across roles
- [ ] Bullet count per role is correct (4-5 most recent, 2-3 older)
- [ ] Seniority language matches career level
- [ ] No personal pronouns (I, me, my)

### Consistency
- [ ] Title in header matches title in Summary
- [ ] Dates are correct and chronological (no overlaps or backwards ranges)
- [ ] No typos or incomplete sentences
- [ ] Tense is consistent (past tense for past roles, present for current)
- [ ] Date format is consistent throughout (Mon YYYY – Mon YYYY)

### Skills & Tools
- [ ] Skills grouped into 3 categories (Design, Research, Collaboration)
- [ ] Tools on a single line
- [ ] No redundant or outdated tools listed

### Review Output Format

Structure the review as:

```
## Resume Review: [Candidate Name]

### Overall Assessment
[1-2 sentence verdict]

### Section Ratings
| Section | Rating |
|---------|--------|
| Contact & Portfolio | Strong / Needs Work / Critical Issue |
| Summary | ... |
| Experience | ... |
| Key Projects | ... |
| Education | ... |
| Skills & Tools | ... |

### Issues & Suggested Rewrites

#### 1. [Section] — [Issue title]
**Issue:** [What's wrong]
**Why it matters:** [Recruiter impact]
**Before:** [Current text]
**Suggested:** [Rewritten text]

#### 2. ...

### Top Actions
[Numbered list of 3-5 highest-priority fixes]

---
Want me to generate a full rewrite with all these fixes applied?
```
