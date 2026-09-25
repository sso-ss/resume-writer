"""Export the editorial resume as a PDF with an extractable text layer."""

import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright
from pypdf import PdfReader

from to_html_editorial import build_html


def build_pdf(md_path, pdf_path, layout="editorial-html", accent_color=None):
    output = Path(pdf_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="resume-pdf-") as directory:
        html = Path(directory) / "resume.html"
        build_html(str(md_path), str(html), layout)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page(viewport={"width": 1000, "height": 1200})
                page.route("https://**/*", lambda route: route.abort())
                page.goto(html.as_uri(), wait_until="load", timeout=15000)
                if accent_color:
                    page.locator("body").evaluate("(body, color) => body.style.setProperty('--accent', color)", accent_color)
                page.pdf(path=str(output), prefer_css_page_size=True, print_background=True,
                         display_header_footer=False, tagged=True)
            finally:
                browser.close()
    pdf = PdfReader(output)
    if not any((page.extract_text() or "").strip() for page in pdf.pages):
        output.unlink()
        raise RuntimeError("PDF export has no readable text.")
    return str(output)