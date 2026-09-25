import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from render_review import build_html, create_server


class ResumeReviewRendererTests(unittest.TestCase):
    def test_exact_quote_creates_linked_highlight_and_annotation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resume = root / "Jordan_Lee_Resume.md"
            resume.write_text(
                "# Jordan Lee\n\nhttps://portfolio.example | jordan@example.com\n\n"
                "## Experience\n\n### Product Designer | Example Co | 2024 – Present\n"
                "- Designed dashboards for users.\n",
                encoding="utf-8",
            )
            review = root / "review.json"
            review.write_text(json.dumps({
                "candidate": "Jordan Lee",
                "overall": "The experience needs stronger evidence.",
                "strengths": ["Clear role title"],
                "target_job": {
                    "title": "Senior Product Designer",
                    "company": "Acme",
                    "source": "https://jobs.example/senior-product-designer",
                    "summary": "The role emphasizes analytics workflows and measurable outcomes.",
                    "requirements": [{
                        "requirement": "Design analytics workflows",
                        "priority": "core",
                        "status": "partial-match",
                        "evidence_quotes": ["Designed dashboards for users."],
                        "feedback": "The dashboard work is relevant, but its scale and outcome are unclear.",
                    }],
                },
                "bullet_reviews": [{
                    "section": "Experience",
                    "quote": "Designed dashboards for users.",
                    "rating": "needs-work",
                    "assessment": "The action is clear, but scope, method, and outcome are missing.",
                    "strengths": ["Starts with a direct design action"],
                    "gaps": ["No product scope", "No method", "No outcome"],
                    "suggestion": "Designed [dashboard scope] by [method], improving [verified outcome].",
                    "job_alignment": "partial-match",
                    "job_feedback": "Relevant to the analytics requirement, but evidence is incomplete.",
                }],
                "findings": [{
                    "section": "Experience",
                    "severity": "important",
                    "title": "Outcome is missing",
                    "quote": "Designed dashboards for users.",
                    "issue": "The bullet describes activity without an outcome.",
                    "why": "Recruiters cannot judge scope or impact.",
                    "suggestion": "Designed [dashboard scope], improving [verified outcome] by [verified amount].",
                }],
            }), encoding="utf-8")
            output = root / "review.html"

            build_html(resume, review, output)

            html = output.read_text(encoding="utf-8")
            self.assertIn("<mark>Designed dashboards for users.</mark>", html)
            self.assertIn('data-notes="note-1"', html)
            self.assertIn('id="note-1"', html)
            self.assertIn('data-bullet-review="bullet-note-1"', html)
            self.assertIn('>B1</button>', html)
            self.assertIn('class="review-tag needs-work">B1</span>', html)
            self.assertIn("Bullet-by-bullet content review", html)
            self.assertIn("No product scope", html)
            self.assertIn('data-job-matches="job-note-1"', html)
            self.assertIn('class="review-tag partial-match">J1</span>', html)
            self.assertIn("Job requirement match", html)
            self.assertIn("Design analytics workflows", html)
            self.assertIn("Relevant to the analytics requirement", html)
            self.assertIn("View job posting", html)
            self.assertIn('id="change-job"', html)
            self.assertIn('id="job-update-form"', html)
            self.assertNotIn("border-left:", html)
            self.assertIn("--green-soft:#eaf3ee", html)
            self.assertNotIn("Anchor not found", html)

    def test_every_experience_and_project_bullet_requires_content_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resume = root / "Jordan_Lee_Resume.md"
            resume.write_text(
                "# Jordan Lee\n\n## Experience\n- Designed one flow.\n- Designed another flow.\n",
                encoding="utf-8",
            )
            review = root / "review.json"
            review.write_text(json.dumps({
                "findings": [],
                "target_job": {
                    "title": "Product Designer",
                    "company": "Acme",
                    "source": "User-provided job description",
                    "summary": "The role requires product design execution.",
                    "requirements": [{
                        "requirement": "Product design execution",
                        "priority": "core",
                        "status": "partial-match",
                        "evidence_quotes": ["Designed one flow."],
                        "feedback": "One relevant example is visible.",
                    }],
                },
                "bullet_reviews": [{
                    "section": "Experience",
                    "quote": "Designed one flow.",
                    "rating": "needs-work",
                    "assessment": "The outcome is missing.",
                    "strengths": ["Clear action"],
                    "gaps": ["No outcome"],
                    "suggestion": "Designed [flow], improving [verified outcome].",
                    "job_alignment": "partial-match",
                    "job_feedback": "The action is relevant but lacks evidence.",
                }],
            }), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Every Experience and Projects bullet"):
                build_html(resume, review, root / "review.html")

    def test_job_match_rejects_evidence_not_found_in_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resume = root / "Jordan_Lee_Resume.md"
            resume.write_text("# Jordan Lee\n\n## Experience\n- Designed one flow.\n", encoding="utf-8")
            review = root / "review.json"
            review.write_text(json.dumps({
                "findings": [],
                "target_job": {
                    "title": "Product Designer", "company": "Acme",
                    "source": "User-provided job description",
                    "summary": "The role requires research.",
                    "requirements": [{
                        "requirement": "Lead generative research", "priority": "core",
                        "status": "strong-match", "evidence_quotes": ["Conducted 20 interviews."],
                        "feedback": "The resume appears to show research evidence.",
                    }],
                },
                "bullet_reviews": [{
                    "section": "Experience", "quote": "Designed one flow.", "rating": "needs-work",
                    "assessment": "Outcome is missing.", "strengths": ["Clear action"],
                    "gaps": ["No outcome"], "suggestion": "Designed [flow], improving [outcome].",
                    "job_alignment": "not-relevant", "job_feedback": "This bullet does not support research."
                }],
            }), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Job-match evidence must quote visible resume text"):
                build_html(resume, review, root / "review.html")

    def test_job_match_requires_posting_url_or_pasted_description(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resume = root / "Jordan_Lee_Resume.md"
            resume.write_text("# Jordan Lee\n\n## Experience\n- Designed one flow.\n", encoding="utf-8")
            review = root / "review.json"
            review.write_text(json.dumps({
                "findings": [],
                "target_job": {
                    "title": "Product Designer", "company": "Acme",
                    "source": "User-provided target role",
                    "summary": "Generic role-level expectations.",
                    "requirements": [{
                        "requirement": "Product design", "priority": "core",
                        "status": "partial-match", "evidence_quotes": ["Designed one flow."],
                        "feedback": "The resume shows one design example.",
                    }],
                },
                "bullet_reviews": [{
                    "section": "Experience", "quote": "Designed one flow.",
                    "rating": "needs-work", "assessment": "Outcome is missing.",
                    "strengths": ["Clear action"], "gaps": ["No outcome"],
                    "suggestion": "Designed [flow], improving [outcome].",
                    "job_alignment": "partial-match",
                    "job_feedback": "The action is relevant but lacks evidence.",
                }],
            }), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "job posting URL or 'User-provided job description'"):
                build_html(resume, review, root / "review.html")

    def test_preview_saves_pending_job_update(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            html = root / "review.html"
            resume = root / "resume.md"
            review = root / "review.json"
            html.write_text("<html><head></head><body>Review</body></html>", encoding="utf-8")
            resume.write_text("# Jordan Lee", encoding="utf-8")
            review.write_text("{}", encoding="utf-8")
            server = create_server(html, resume, review)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                origin = f"http://127.0.0.1:{server.server_port}"
                with urllib.request.urlopen(origin) as response:
                    page = response.read().decode("utf-8")
                token = page.split('name="review-update-token" content="', 1)[1].split('"', 1)[0]
                request = urllib.request.Request(
                    f"{origin}/update-job",
                    data=json.dumps({"source": "https://jobs.example/product-designer"}).encode("utf-8"),
                    headers={"Content-Type": "application/json", "Origin": origin, "X-Review-Token": token},
                    method="POST",
                )
                with urllib.request.urlopen(request) as response:
                    result = json.loads(response.read())
                saved = root / result["request_file"]
                payload = json.loads(saved.read_text(encoding="utf-8"))
                self.assertEqual("pending", payload["status"])
                self.assertEqual("url", payload["source_type"])
                self.assertEqual("https://jobs.example/product-designer", payload["source"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join()


if __name__ == "__main__":
    unittest.main()