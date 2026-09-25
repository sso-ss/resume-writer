import io
import json
import re
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from docx import Document
from pypdf import PdfReader
from playwright.sync_api import sync_playwright
from serve_resume import WORD_BUILDERS, create_server
from to_docx_right_sidebar_refined import build_layout_refined
from to_html_editorial import build_html


class ResumeServerTests(unittest.TestCase):
    def test_pdf_button_download_preserves_browser_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "resume.md"
            source.write_text("# Original Name\n\nname@example.com\n\n## Summary\n\nOriginal summary\n")
            html = build_html(str(source), str(Path(directory) / "resume.html"))
            server = create_server(html, "editorial-html")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch()
                    try:
                        page = browser.new_page()
                        page.route("https://**/*", lambda route: route.abort())
                        page.goto(f"http://127.0.0.1:{server.server_port}/")
                        page.locator("h1").fill("Browser Edited Name")
                        with page.expect_download() as result:
                            page.get_by_role("button", name="Save as PDF").click()
                        download = result.value
                        self.assertEqual(download.suggested_filename, "Browser_Edited_Name_Resume.pdf")
                        output = Path(directory) / "download.pdf"
                        download.save_as(output)
                        pdf = PdfReader(output)
                        self.assertIn("Browser Edited Name", pdf.pages[0].extract_text())
                        self.assertEqual(len(pdf.pages), 1)
                    finally:
                        browser.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join()

    def test_all_document_layouts_have_word_generators(self):
        self.assertEqual(
            set(WORD_BUILDERS),
            {"single-column", "two-column-left", "two-column-right", "two-column-right-refined", "editorial-html"},
        )
        with self.assertRaisesRegex(ValueError, "Unknown resume layout"):
            create_server("missing.html", "unknown")

    def test_standalone_refined_layout_keeps_header_divider(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "resume.md"
            output = Path(directory) / "resume.docx"
            source.write_text("# Name\n\nname@example.com\n\n## Summary\n\nSummary\n")
            build_layout_refined(str(source), str(output))
            document = Document(output)
            self.assertEqual(len(document.element.xpath(".//w:pBdr/w:bottom")), 1)

    def test_export_uses_python_generator_and_rejects_foreign_requests(self):
        with tempfile.TemporaryDirectory() as directory:
            html = Path(directory) / "resume.html"
            html.write_text("<head></head><body>Resume</body>")
            server = create_server(html, "two-column-right-refined")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                origin = f"http://127.0.0.1:{server.server_port}"
                preview = urlopen(origin).read().decode()
                token = re.search(r'content="([^"]+)"', preview).group(1)
                markdown = (
                    "# Edited Name\n\nPortfolio: https://example.com | test@example.com\n\n"
                    "## Summary\n\nEdited summary\n\n## Experience\n\n"
                    "### Designer | Edited Company | 2024 - Present\n- Edited achievement\n\n"
                    "## Education\n\nEdited degree\n"
                )
                body = json.dumps({"markdown": markdown}).encode()
                headers = {"Content-Type": "application/json", "Origin": origin, "X-Resume-Token": token}
                request = Request(origin + "/export-word", data=body, headers=headers)
                document = Document(io.BytesIO(urlopen(request).read()))
                text = "\n".join(paragraph.text for paragraph in document.paragraphs)
                text += "\n".join(cell.text for table in document.tables for row in table.rows for cell in row.cells)
                for expected in ("Edited Name", "Edited Company", "Edited achievement", "Edited degree"):
                    self.assertIn(expected, text)
                self.assertEqual(len(document.tables[0].columns), 2)
                self.assertEqual(len(document.element.xpath(".//w:pBdr/w:bottom")), 1)
                response = urlopen(Request(origin + "/export-pdf", data=body, headers=headers))
                self.assertEqual(response.headers["Content-Type"], "application/pdf")
                pdf = PdfReader(io.BytesIO(response.read()))
                pdf_text = " ".join(" ".join(page.extract_text() or "" for page in pdf.pages).split())
                for expected in ("Edited Name", "Edited Company", "Edited achievement", "Edited degree", "EXPERIENCE", "EDUCATION"):
                    self.assertIn(expected, pdf_text)
                self.assertLess(pdf_text.index("Edited achievement"), pdf_text.index("Edited degree"))
                self.assertEqual(len(pdf.pages), 1)
                self.assertIsNotNone(pdf.trailer["/Root"].get("/StructTreeRoot"))
                for bad_headers in ({}, {**headers, "Origin": "https://example.com"}):
                    with self.assertRaises(HTTPError) as error:
                        urlopen(Request(origin + "/export-word", data=body, headers=bad_headers))
                    self.assertEqual(error.exception.code, 403)
                with self.assertRaises(HTTPError) as error:
                    urlopen(origin + "/../Jennifer_Lauren_Resume.md")
                self.assertEqual(error.exception.code, 404)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()


if __name__ == "__main__":
    unittest.main()