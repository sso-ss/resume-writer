import unittest
import tempfile
from pathlib import Path

from lxml import html

from to_html_editorial import build_html, jobs_html


class EditorialHeaderTests(unittest.TestCase):
    def test_selected_layout_controls_preview_structure(self):
        markdown = "# Name\n\nPortfolio: https://example.com\n\n## Summary\n\nProduct Designer summary\n"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "Name_Resume.md"
            source.write_text(markdown)
            for layout in ("single-column", "two-column-left", "two-column-right", "two-column-right-refined", "editorial-html"):
                output = Path(build_html(str(source), str(Path(directory) / f"{layout}.html"), layout))
                document = html.fromstring(output.read_text())
                self.assertEqual(document.find("body").get("data-layout"), layout)
                self.assertEqual(document.xpath('//div[@class="toolbar"]/p')[0].text_content(), layout.replace("-", " ").title() + " preview")
            with self.assertRaisesRegex(ValueError, "Unknown resume layout"):
                build_html(str(source), layout="unknown")

    def test_job_header_groups_title_company_and_date(self):
        job = html.fromstring(jobs_html([
            '### Product Designer | ExampleCo | Jul 2024 - Present',
            '- Improved onboarding',
        ]))
        header = job.find('div')
        self.assertEqual(header.get('class'), 'job-header')
        self.assertEqual(header.find('h3').text_content(), 'Product Designer | ExampleCo')
        self.assertEqual(header.find('p').text_content(), 'Jul 2024 - Present')
        self.assertEqual(job.find('ul/li').text, 'Improved onboarding')
        self.assertEqual(len(job.xpath('.//*[@class="meta"]')), 1)

    def test_missing_company_does_not_leave_separator(self):
        job = html.fromstring(jobs_html(['### Designer']))
        self.assertEqual(job.find('div/h3').text_content(), 'Designer')

    def test_header_escapes_source_text(self):
        job = html.fromstring(jobs_html(['### Design <Lead> | A & B | <2024>']))
        self.assertEqual(job.find('div/h3').text_content(), 'Design <Lead> | A & B')
        self.assertEqual(job.find('div/p').text_content(), '<2024>')
        self.assertEqual(len(job.xpath('.//lead')), 0)


if __name__ == '__main__':
    unittest.main()