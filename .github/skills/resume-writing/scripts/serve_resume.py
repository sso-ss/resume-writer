#!/usr/bin/env python3
"""Serve an editable resume and export edits with the existing Python Word generator."""

import argparse
import json
import secrets
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from to_docx import create_resume_doc
from to_docx_editorial import build_layout_editorial
from to_docx_right_sidebar import build_layout_c
from to_docx_right_sidebar_refined import build_layout_refined
from to_docx_two_column import build_layout_b
from to_html_editorial import build_html


WORD_BUILDERS = {
    "single-column": create_resume_doc,
    "two-column-left": build_layout_b,
    "two-column-right": build_layout_c,
    "two-column-right-refined": build_layout_refined,
    "editorial-html": build_layout_editorial,
}


def create_server(html_path, layout="editorial-html", port=0):
    html_path = Path(html_path).resolve()
    if layout not in WORD_BUILDERS:
        raise ValueError(f"Unknown resume layout: {layout}")
    word_builder = WORD_BUILDERS[layout]
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def respond(self, code, content, content_type):
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self):
            if self.path != "/":
                self.respond(404, b"Not found", "text/plain")
                return
            html = html_path.read_text(encoding="utf-8").replace(
                "</head>", f'<meta name="word-export-token" content="{token}"></head>'
            )
            self.respond(200, html.encode("utf-8"), "text/html; charset=utf-8")

        def do_POST(self):
            if self.path not in ("/export-word", "/export-pdf"):
                self.respond(404, b"Not found", "text/plain")
                return
            origin = f"http://127.0.0.1:{self.server.server_port}"
            if (self.headers.get("Origin") != origin
                    or self.headers.get("X-Resume-Token") != token):
                self.respond(403, b"Open the local resume preview before exporting.", "text/plain")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 262144:
                    raise ValueError("Invalid resume size")
                data = json.loads(self.rfile.read(length))
                markdown = data["markdown"]
                if not isinstance(markdown, str) or not markdown.startswith("# "):
                    raise ValueError("Invalid resume content")
                editorial_header = data.get("editorial_header", {})
                if not isinstance(editorial_header, dict) or any(
                    key not in ("eyebrow", "role") or not isinstance(value, str)
                    for key, value in editorial_header.items()
                ):
                    raise ValueError("Invalid editorial header")
            except (ValueError, KeyError, TypeError):
                self.respond(400, b"Invalid resume content", "text/plain")
                return
            try:
                with tempfile.TemporaryDirectory(prefix="resume-export-") as directory:
                    source = Path(directory) / "resume.md"
                    is_pdf = self.path == "/export-pdf"
                    output = Path(directory) / ("resume.pdf" if is_pdf else "resume.docx")
                    source.write_text(markdown, encoding="utf-8")
                    if is_pdf:
                        from to_pdf_editorial import build_pdf
                        build_pdf(str(source), str(output), layout)
                    elif layout == "editorial-html":
                        word_builder(str(source), str(output), editorial_header=editorial_header)
                    else:
                        word_builder(str(source), str(output))
                    content = output.read_bytes()
            except Exception:
                self.respond(500, b"Export failed. Your browser edits are unchanged.", "text/plain")
                return
            content_type = "application/pdf" if is_pdf else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            self.respond(200, content, content_type)

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown")
    parser.add_argument("html", nargs="?")
    parser.add_argument("--layout", choices=WORD_BUILDERS, default="editorial-html")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    html_path = build_html(args.markdown, args.html, args.layout)
    server = create_server(html_path, args.layout, args.port)
    print(f"Resume preview: http://127.0.0.1:{server.server_port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()