---
name: resume-review
description: Reviews uploaded Product Designer resumes against a target job and generates annotated HTML with requirement matches, highlighted issues, bullet-level alignment, and evidence-based revisions. Use when a user uploads a Markdown or Word resume and asks for review, critique, job matching, feedback, or what to fix.
argument-hint: "Upload a resume and provide a target job URL or description"
---

# Product Designer Resume Review

## Scope

Review an existing resume against the user's target job. Do not rewrite the full resume unless the user approves after seeing the review. This is a qualitative, evidence-based recruiter review, not an ATS certification or numeric match score.

Supported uploads: `.md` and `.docx`.

## Workflow

1. Identify the uploaded resume and target job posting. Accept either a public job-posting URL or the complete job description pasted by the user.
2. If no posting was provided, stop and ask: "Please share the job posting URL or paste the full job description so I can review and match your resume against it." Do not substitute a sample posting, infer requirements from a title/company, or generate the matched review yet.
3. Fetch a provided URL or parse the pasted description, then extract the exact role title, company, product context, and top 5-7 requirements. Prefer the employer's official posting over aggregators. Set `target_job.source` to the URL or exactly `User-provided job description`.
4. Read [recruiter-guidelines.md](../resume-writing/references/recruiter-guidelines.md).
5. Extract the visible blocks, especially for Word files:

   ```bash
   python3 .github/skills/resume-review/scripts/render_review.py <resume-file> --extract
   ```

6. Compare the resume against each core and preferred job requirement. Cite exact resume evidence for every match.
7. Review every section and every Experience and Projects bullet; do not sample only a few bullets.
8. Save structured findings as `output/reviews/<ResumeStem>_Review.json` using the schema below.
9. Validate every evidence quote and annotation quote against extracted visible text.
10. Generate and serve the annotated review:

   ```bash
   python3 .github/skills/resume-review/scripts/render_review.py <resume-file> output/reviews/<ResumeStem>_Review.json --serve
   ```

11. Open the printed localhost URL. Confirm job evidence and annotations link to the intended text and that the page works at desktop and mobile widths.
12. Give the user the review URL and summarize the top 3 changes that would improve fit. Tell them they can provide another URL or pasted job description at any time to refresh the matching analysis.

## Changing The Target Job

When the user provides a different posting for the same resume:

1. Fetch or parse the new posting from scratch; do not reuse requirements from the previous job.
2. Replace the complete `target_job` object and recalculate every requirement status, evidence link, `job_alignment`, `job_feedback`, overall summary, and top recommendation.
3. Preserve resume-grounded content observations only when they remain valid independently of the old posting.
4. Regenerate the JSON and HTML, replacing the current review unless the user asks to keep both versions.

The served preview includes **Change job**. It accepts a public URL or a pasted full description and saves `<ReviewStem>_Job_Update.json` beside the HTML. When the user says "Apply the job update from the preview":

1. Find the pending update file associated with the current review and read its `source_type` and `source`.
2. Process it as the new posting using the steps above; never treat the saved request itself as completed analysis.
3. After regeneration, change its `status` from `pending` to `processed` so the same request is not applied twice.

## Review Rubric

Evaluate:

- **Positioning:** target role, seniority, domain, and differentiator are immediately clear.
- **Contact:** portfolio is prominent and contact details are complete.
- **Summary:** concise, specific, evidence-based, and free of generic claims.
- **Experience:** bullets communicate ownership, method, scope, and verified outcomes; current and past tense are correct.
- **Projects:** selected work has working case-study URLs and demonstrates relevant range.
- **Skills:** credible, grouped, role-relevant, and not duplicated by a tool inventory.
- **Structure:** standard headings, reverse chronology, concise length, and fast recruiter scanability.
- **Integrity:** no invented metrics, inflated ownership, unsupported causality, or unverified claims.

For every Experience and Projects bullet, assess:

- **Action and ownership:** what the candidate personally did is specific.
- **Scope and context:** the product, users, team, scale, or problem is understandable.
- **Method:** relevant design or research decisions explain how the work was done.
- **Outcome and evidence:** the result is concrete, credible, and appropriately attributed.
- **Clarity:** the bullet is concise, readable, and distinct from nearby bullets.

Mark the bullet `strong` only when its content is interview-ready. Mark it `needs-work` when evidence, context, method, attribution, or clarity is materially missing.

For target-job matching:

- Extract requirements from the actual posting; do not infer specific requirements the employer did not state.
- Mark `strong-match` only when the resume contains direct, credible evidence.
- Mark `partial-match` when evidence is adjacent, incomplete, buried, or uses weaker framing.
- Mark `gap` when the resume contains no evidence. A gap means “not demonstrated in this resume,” not “the candidate lacks this skill.”
- Separate core requirements from preferred qualifications.
- Recommend exact job language only when it truthfully describes the candidate's existing experience.

Use severity consistently:

- `critical`: likely to block recruiter understanding or credibility.
- `important`: materially weakens positioning or evidence.
- `polish`: useful improvement that does not change the core candidacy signal.

## Review JSON

```json
{
  "candidate": "Candidate Name",
  "overall": "One or two sentences describing the resume's strongest signal and largest gap.",
  "strengths": [
    "Specific strength grounded in the resume"
  ],
  "target_job": {
    "title": "Senior Product Designer",
    "company": "Company Name",
    "source": "Official job URL or 'User-provided job description'",
    "summary": "One sentence describing the role's strongest hiring signals.",
    "requirements": [
      {
        "requirement": "Exact or closely paraphrased requirement from the posting",
        "priority": "core",
        "status": "strong-match",
        "evidence_quotes": ["Exact visible resume text supporting this match"],
        "feedback": "What matches and what would improve the evidence or positioning."
      }
    ]
  },
  "bullet_reviews": [
    {
      "section": "Experience",
      "quote": "The complete exact visible bullet text",
      "rating": "strong",
      "assessment": "Why this bullet is or is not persuasive.",
      "strengths": ["Clear ownership", "Verified outcome"],
      "gaps": [],
      "suggestion": "Keep as written, or provide a truthful improved bullet using only known evidence.",
      "job_alignment": "strong-match",
      "job_feedback": "How this bullet supports the target job, or why it is not relevant."
    }
  ],
  "findings": [
    {
      "section": "Experience",
      "severity": "important",
      "title": "Outcome is missing",
      "quote": "Exact visible text from one extracted block",
      "issue": "What is weak or unclear.",
      "why": "How this affects a recruiter's decision.",
      "suggestion": "A truthful revision using only known evidence, or bracketed placeholders for missing facts."
    }
  ]
}
```

## Annotation Rules

- Include 5-7 prioritized job requirements when the posting provides enough detail.
- Every `strong-match` or `partial-match` requirement must cite at least one exact visible resume quote. A `gap` must have no evidence quote.
- Add `job_alignment` and `job_feedback` to every bullet review. Use `not-relevant` when a valid bullet does not support the target role's main requirements; do not weaken it merely to force keyword overlap.
- Do not produce a numeric match score or imply ATS certification.
- Never turn an absent requirement into claimed experience. Suggest a truthful clarification or mark it as not demonstrated.
- Include exactly one `bullet_reviews` entry for every visible bullet in Experience, Work Experience, Professional Experience, Projects, Key Projects, and Selected Projects.
- Use the complete visible bullet as the bullet-review `quote`; the renderer rejects partial, duplicate, or missing bullet coverage.
- Review bullet content, not only grammar or formatting. Explain the ownership, context, method, outcome, evidence, and credibility signal.
- For a strong bullet, explain why it works and use `Keep as written.` when no rewrite is needed.
- Anchor each finding to the smallest exact quote that makes the issue understandable.
- Do not attach several generic findings to an entire section when a specific bullet is responsible.
- Combine overlapping observations into one annotation.
- Keep the annotation useful without requiring chat context.
- Never fabricate a number. Use `[verified metric]`, `[scope]`, or `[outcome]` when evidence is missing.
- Include strengths separately; do not manufacture issues to fill every section.
- If an anchor is reported as missing, correct the JSON and regenerate before presenting the page.

## Review Completion

The review is complete only when:

- the user supplied a job-posting URL or pasted job description; no sample or inferred posting was used;
- every finding appears in the annotation rail;
- every finding is linked to highlighted resume text;
- every job-match claim is linked to exact resume evidence, while gaps are clearly labeled as not demonstrated;
- every Experience and Projects bullet has a linked content review, including strong bullets;
- no `Anchor not found` warning remains;
- suggestions preserve the candidate's meaning and evidence;
- the localhost page has been opened and visually checked.