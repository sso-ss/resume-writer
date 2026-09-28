import tempfile
import threading
import unittest
from pathlib import Path

from docx import Document
from lxml import html
from playwright.sync_api import sync_playwright

from serve_resume import create_server
from to_html_editorial import build_html


LAYOUTS = (
    "single-column", "two-column-left", "two-column-right",
    "two-column-right-refined", "editorial-html",
)
SOURCE = """# Test Designer

Portfolio: https://example.com | designer@example.com

## Experience
### Product Designer | Example Studio | Jan 2024 – Present
- Resolved competing workflow requirements with product and engineering; the agreed permission model shipped in the admin portal.

## Skills & Tools
- **Design:** Interaction Design, Information Architecture
- **Research:** Usability Testing
- **Collaboration & Leadership:** Stakeholder Alignment, Mentoring
- **AI:** AI-assisted Prototyping
- **Tools:** Figma, Claude

## Education
B.Des | Example University | 2020
"""


class OptionalSectionTests(unittest.TestCase):
    def test_optional_sections_stay_absent_in_previews_switching_and_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "resume.md"
            source.write_text(SOURCE)
            for layout in LAYOUTS:
                output = build_html(str(source), str(Path(directory) / f"{layout}.html"), layout)
                tree = html.parse(output)
                self.assertFalse(tree.xpath('//*[@class="summary-label" or @class="intro"]'))
                headings = tree.xpath('//main//h2/text()')
                self.assertNotIn("Selected Projects", headings)
                self.assertNotIn("Recognition", headings)
            server = create_server(output)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch()
                    try:
                        page = browser.new_page()
                        page.route('https://**/*', lambda route: route.abort())
                        page.goto(f'http://127.0.0.1:{server.server_port}/')
                        page.locator('.job li').fill('Aligned partners on the permission model; the revised admin portal shipped.')
                        for layout in LAYOUTS:
                            with self.subTest(layout=layout):
                                page.locator('#preview-layout').select_option(layout)
                                self.assertEqual(page.locator('.summary-label, .intro').count(), 0)
                                text = page.locator('main.page').inner_text()
                                self.assertNotIn('null', text)
                                self.assertNotIn('Selected Projects', text)
                                self.assertNotIn('Recognition', text)
                                markdown = page.evaluate('resumeMarkdown(document.querySelector("main.page"))')
                                self.assertNotIn('## Summary', markdown)
                                with page.expect_download() as result:
                                    page.get_by_role('button', name='Save as Word', exact=True).click()
                                exported = Path(directory) / f'{layout}.docx'
                                result.value.save_as(exported)
                                document = Document(exported)
                                text = '\n'.join(document.element.xpath('.//w:t/text()'))
                                self.assertIn('Aligned partners on the permission model', text)
                                self.assertIn('Stakeholder Alignment, Mentoring', text)
                                self.assertIn('AI-assisted Prototyping', text)
                                self.assertIn('Example University', text)
                                self.assertNotIn('SUMMARY', text.upper())
                                self.assertNotIn('PROJECTS', text.upper())
                                self.assertNotIn('RECOGNITION', text.upper())
                    finally:
                        browser.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join()


if __name__ == '__main__':
    unittest.main()
