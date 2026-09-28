"""Local upload → skill-guided analysis → annotated resume review."""
from __future__ import annotations

import base64
import binascii
import copy
import json
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import threading
import time
import zipfile
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from render_review import (build_html, extract_blocks, load_review, match_findings,
                           normalize, REVIEWED_BULLET_SECTIONS)

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "templates" / "review-start.html"
MAX_FILE = 5 * 1024 * 1024
MAX_BODY = 7 * 1024 * 1024
PROVIDERS = {"codex": "Codex", "claude": "Claude Code", "cursor": "Cursor", "copilot": "GitHub Copilot"}
PROVIDER_COMMANDS = {"codex": ("codex",), "claude": ("claude",),
                     "cursor": ("cursor-agent", "agent"), "copilot": ("copilot",)}
PROVIDER_SETUP = {
    "codex": "Install Codex CLI, run codex, and sign in.",
    "claude": "Install Claude Code, run claude, and sign in.",
    "cursor": "Install Cursor Agent CLI and run agent login with your Cursor account.",
    "copilot": "Install GitHub Copilot CLI, run copilot, and sign in with your GitHub account.",
}


def provider_executable(provider):
    return next((path for command in PROVIDER_COMMANDS[provider]
                 if (path := shutil.which(command))), None)


def detect_provider(provider="auto", environ=None):
    if provider != "auto":
        if provider not in PROVIDERS:
            raise ReviewError("Choose an AI tool for this review.")
        return provider
    environ = os.environ if environ is None else environ
    detected = [name for name, marker in (("claude", "CLAUDECODE"), ("codex", "CODEX_THREAD_ID"))
                if environ.get(marker)]
    # Installation alone does not establish which account the user wants to use.
    return detected[0] if len(detected) == 1 else ""


def provider_config(provider):
    return {"selected": provider, "providers": [
        {"id": key, "name": name, "installed": bool(provider_executable(key)), "setup": PROVIDER_SETUP[key]}
        for key, name in PROVIDERS.items()]}


def object_schema(**properties):
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def array_schema(items):
    return {"type": "array", "items": items}


STRING = {"type": "string"}
STRINGS = array_schema(STRING)
REVIEW_SCHEMA = object_schema(
    candidate=STRING, overall=STRING, strengths=STRINGS,
    target_job=object_schema(
        title=STRING, company=STRING, source=STRING, summary=STRING,
        requirements=array_schema(object_schema(
            requirement=STRING, priority={"enum": ["core", "preferred"], "type": "string"},
            status={"enum": ["strong-match", "partial-match", "gap"], "type": "string"},
            evidence_quotes=STRINGS, feedback=STRING,
        )),
    ),
    bullet_reviews=array_schema(object_schema(
        section=STRING, quote=STRING, rating={"enum": ["strong", "needs-work"], "type": "string"},
        assessment=STRING, strengths=STRINGS, gaps=STRINGS, suggestion=STRING,
        job_alignment={"enum": ["strong-match", "partial-match", "not-relevant"], "type": "string"},
        job_feedback=STRING,
    )),
    findings=array_schema(object_schema(
        section=STRING, severity={"enum": ["critical", "important", "polish"], "type": "string"},
        title=STRING, quote=STRING, issue=STRING, why=STRING, suggestion=STRING,
    )),
)
# Preserve the saved format, adding optional IDs to disambiguate repeated text.
COMPACT_REVIEW_SCHEMA = copy.deepcopy(REVIEW_SCHEMA)


def replace_fields(schema, removed, **added):
    for key in removed:
        del schema["properties"][key]
    schema["properties"].update(added)
    schema["required"] = list(schema["properties"])


replace_fields(COMPACT_REVIEW_SCHEMA, ["candidate"])
replace_fields(COMPACT_REVIEW_SCHEMA["properties"]["target_job"], ["source"])
replace_fields(COMPACT_REVIEW_SCHEMA["properties"]["target_job"]["properties"]["requirements"]["items"],
               ["evidence_quotes"], evidence_ids=STRINGS)
replace_fields(COMPACT_REVIEW_SCHEMA["properties"]["bullet_reviews"]["items"],
               ["section", "quote"], block_id=STRING)
replace_fields(COMPACT_REVIEW_SCHEMA["properties"]["findings"]["items"],
               ["section", "quote"], block_id=STRING, excerpt=STRING)
COMPACT_OUTPUT_SCHEMA = object_schema(
    review={"anyOf": [COMPACT_REVIEW_SCHEMA, {"type": "null"}]}, error=STRING)


def prepared_blocks(blocks):
    return [{"id": f"r{index + 1}", **block.__dict__} for index, block in enumerate(blocks)]


def reviewable_ids(blocks):
    return {f"r{index + 1}" for index, block in enumerate(blocks)
            if block.kind == "bullet" and normalize(block.section) in REVIEWED_BULLET_SECTIONS}


def expand_review(compact, blocks, source, source_type):
    """Resolve model references against this upload, rejecting incomplete coverage."""
    review = copy.deepcopy(compact)
    indexed = {item["id"]: item for item in prepared_blocks(blocks)}

    def resolve(identifier):
        if not isinstance(identifier, str) or identifier not in indexed:
            raise ValueError(f"Unknown resume block ID: {identifier!r}")
        return indexed[identifier]

    review["candidate"] = next((block.text for block in blocks if block.kind == "name"), "Candidate")
    review["target_job"]["source"] = source if source_type == "url" else "User-provided job description"
    for requirement in review["target_job"]["requirements"]:
        ids = requirement.pop("evidence_ids")
        if not isinstance(ids, list):
            raise ValueError("evidence_ids must be an array")
        requirement["evidence_quotes"] = [resolve(identifier)["text"] for identifier in ids]
        requirement["evidence_ids"] = ids
    expected = reviewable_ids(blocks)
    seen = set()
    for bullet in review["bullet_reviews"]:
        block = resolve(bullet["block_id"])
        if block["id"] not in expected or block["id"] in seen:
            raise ValueError(f"Duplicate or non-reviewable bullet ID: {block['id']}")
        seen.add(block["id"])
        bullet.update(section=block["section"], quote=block["text"])
    if seen != expected:
        raise ValueError(f"Missing bullet IDs: {', '.join(sorted(expected - seen))}")
    for finding in review["findings"]:
        block = resolve(finding["block_id"])
        excerpt = finding.pop("excerpt")
        if not isinstance(excerpt, str) or (excerpt and excerpt not in block["text"]):
            raise ValueError(f"Finding excerpt must be exact text from {block['id']}")
        finding.update(section=block["section"], quote=excerpt or block["text"])
    return review


class ReviewError(ValueError):
    """An actionable message that is safe to display in the browser."""


def job_source(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 80000:
        raise ReviewError("Add a job posting URL or paste the full job description (up to 80,000 characters).")
    value = value.strip()
    parsed = urlparse(value)
    if parsed.scheme in ("http", "https") and parsed.netloc and not any(c.isspace() for c in value):
        return value, "url"
    if value.startswith(("http:", "https:", "www.")) or len(value) < 50:
        raise ReviewError("Enter a complete https:// job URL or paste the full job description.")
    return value, "description"


def validate_upload(payload, directory):
    name = payload.get("filename")
    if not isinstance(name, str):
        raise ReviewError("Choose a Word (.docx) or Markdown (.md) resume.")
    suffix = Path(name).suffix.lower()
    if suffix not in (".md", ".docx"):
        raise ReviewError("Choose a Word (.docx) or Markdown (.md) resume.")
    try:
        content = base64.b64decode(payload.get("file", ""), validate=True)
    except (ValueError, TypeError, binascii.Error):
        raise ReviewError("The upload could not be read. Please choose the file again.")
    if not content or len(content) > MAX_FILE:
        raise ReviewError("Choose a non-empty resume smaller than 5 MB.")
    path = directory / f"resume{suffix}"
    path.write_bytes(content)
    try:
        if suffix == ".docx":
            with zipfile.ZipFile(path) as archive:
                if len(archive.infolist()) > 2000 or sum(item.file_size for item in archive.infolist()) > 25 * 1024 * 1024:
                    raise ValueError("Document is too large to unpack")
        blocks = extract_blocks(path)
    except Exception:
        raise ReviewError("This file could not be read. Export it as .docx or UTF-8 Markdown and try again.")
    if not blocks or not any(block.text.strip() for block in blocks):
        raise ReviewError("No readable text was found. Choose a resume containing text.")
    if sum(len(block.text) for block in blocks) > 100000:
        raise ReviewError("This document is too long. Upload only the resume.")
    return path, blocks


def run_codex(prompt, directory):
    executable = shutil.which("codex")
    if not executable:
        raise ReviewError("Automatic review needs Codex CLI. Install it and sign in, then try again.")
    schema = directory / "schema.json"
    result = directory / "analysis.json"
    schema.write_text(json.dumps(COMPACT_OUTPUT_SCHEMA), encoding="utf-8")
    result.unlink(missing_ok=True)
    try:
        # Read-only agent; only the CLI's final structured response is saved. No shell interpolation.
        process = subprocess.run(
            [executable, "exec", "--ephemeral", "--sandbox", "read-only", "--skip-git-repo-check",
             "-c", 'web_search="live"', "--cd", str(directory), "--output-schema", str(schema),
             "--output-last-message", str(result), "-"],
            input=prompt, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=300,
        )
    except subprocess.TimeoutExpired:
        raise ReviewError("The review took too long. Please try again, or paste the job description instead of a URL.")
    except OSError:
        raise ReviewError("Codex could not start. Check that Codex CLI is installed and signed in, then try again.")
    if process.returncode != 0 or not result.is_file():
        # Do not return CLI logs: they can include private input or authentication details.
        raise ReviewError("The review service could not finish. Check your Codex sign-in and connection, then try again.")
    try:
        response = json.loads(result.read_text(encoding="utf-8"))
        if not isinstance(response, dict):
            raise ValueError()
        if response.get("review") is None:
            raise ReviewError("The job details could not be reviewed. Paste the full job description and try again.")
        return response["review"]
    except (json.JSONDecodeError, KeyError):
        raise ReviewError("The review service returned an incomplete result. Please try again.")


def run_claude(prompt, directory):
    executable = shutil.which("claude")
    if not executable:
        raise ReviewError("Install Claude Code, then run claude and sign in before reviewing.")
    environment = os.environ.copy()
    # This is a separate analysis session, not a recursive interactive session.
    environment.pop("CLAUDECODE", None)
    try:
        process = subprocess.run(
            [executable, "-p", "--output-format", "json", "--json-schema", json.dumps(COMPACT_OUTPUT_SCHEMA),
             "--no-session-persistence", "--tools", "WebFetch,WebSearch",
             "--allowedTools", "WebFetch,WebSearch", "--permission-mode", "dontAsk",
             "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
             "--setting-sources", "user", "--settings", '{"disableAllHooks":true}',
             "--disable-slash-commands"],
            input=prompt, text=True, cwd=directory, env=environment,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300,
        )
    except subprocess.TimeoutExpired:
        raise ReviewError("Claude Code took too long. Try again, or paste the job description instead of a URL.")
    except OSError:
        raise ReviewError("Claude Code could not start. Run claude in your terminal and check its setup.")
    try:
        response = json.loads(process.stdout)
        if process.returncode or not isinstance(response, dict) or response.get("is_error"):
            raise ValueError()
        structured = response["structured_output"]
        if not isinstance(structured, dict):
            raise ValueError()
        if structured.get("review") is None:
            raise ReviewError("The job details could not be reviewed. Paste the full job description and try again.")
        if not isinstance(structured["review"], dict):
            raise ValueError()
        return structured["review"]
    except (ValueError, KeyError, TypeError) as error:
        if isinstance(error, ReviewError):
            raise
        # Logs can contain private input and account details; never show them in the page.
        raise ReviewError("Claude Code could not finish. Run claude to check sign-in and account access, "
                          "update Claude Code if needed, then try again.")


def validate_response_schema(value, schema, path="response"):
    """Validate the small JSON Schema subset used by our response contract."""
    if "anyOf" in schema:
        for option in schema["anyOf"]:
            try:
                validate_response_schema(value, option, path)
                return
            except ValueError:
                pass
        raise ValueError(f"{path} does not match the response schema")
    kind = schema.get("type")
    valid = {"object": isinstance(value, dict), "array": isinstance(value, list),
             "string": isinstance(value, str), "null": value is None}
    if kind and not valid[kind]:
        raise ValueError(f"{path} must be {kind}")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"Invalid value for {path}")
    if kind == "object":
        if set(schema["required"]) - value.keys() or value.keys() - schema["properties"].keys():
            raise ValueError(f"{path} has missing or unexpected fields")
        for key, item in value.items():
            validate_response_schema(item, schema["properties"][key], f"{path}.{key}")
    elif kind == "array":
        for index, item in enumerate(value):
            validate_response_schema(item, schema["items"], f"{path}[{index}]")


def run_text_provider(provider, prompt, directory):
    """Adapt CLIs with textual final answers to the same verified JSON contract."""
    executable = provider_executable(provider)
    if not executable:
        raise ReviewError(PROVIDER_SETUP[provider])
    prompt += ("\nReturn only one JSON object matching this schema, without commentary or Markdown fences:\n"
               + json.dumps(COMPACT_OUTPUT_SCHEMA, separators=(",", ":")))
    if provider == "cursor":
        config = directory / ".cursor"
        config.mkdir(exist_ok=True)
        (config / "cli.json").write_text(json.dumps({"permissions": {
            "allow": ["WebFetch(*)"],
            "deny": ["Shell(*)", "Write(**)", "Read(**)", "Mcp(*:*)"],
        }}), encoding="utf-8")
        command = [executable, "--print", "--mode", "ask", "--output-format", "json",
                   "--sandbox", "enabled", "--workspace", str(directory), "--trust"]
    else:
        command = [executable, "--silent", "--stream", "off", "--output-format", "text",
                   "--available-tools=web_fetch", "--allow-tool=url", "--deny-tool=shell,write,read",
                   "--disable-builtin-mcps", "--no-custom-instructions", "--no-ask-user",
                   "--no-remote", "--no-remote-export", "--no-auto-update"]
    try:
        # Both CLIs accept piped input as a noninteractive prompt. Keep private text off argv.
        result = subprocess.run(command, input=prompt, cwd=directory, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
    except subprocess.TimeoutExpired:
        raise ReviewError(f"{PROVIDERS[provider]} took too long. Try again or paste the full job description.")
    except OSError:
        raise ReviewError(PROVIDER_SETUP[provider])
    if result.returncode:
        raise ReviewError(f"{PROVIDERS[provider]} could not finish. {PROVIDER_SETUP[provider]} "
                          "Check account access and update the CLI if needed, then try again.")
    try:
        output = result.stdout.strip()
        if provider == "cursor":
            envelope = json.loads(output)
            if not isinstance(envelope, dict) or envelope.get("is_error") or envelope.get("type") != "result":
                raise ValueError()
            output = envelope["result"].strip()
        fenced = re.fullmatch(r"```(?:json)?\s*\n(.*?)\n```", output, re.DOTALL)
        if fenced:
            output = fenced[1]
        response = json.loads(output)
        validate_response_schema(response, COMPACT_OUTPUT_SCHEMA)
    except (ValueError, KeyError, TypeError, AttributeError):
        raise ReviewError(f"{PROVIDERS[provider]} returned an incomplete review. Try again, or update its CLI.")
    if response["review"] is None:
        raise ReviewError("The job details could not be reviewed. Paste the full job description and try again.")
    return response["review"]


def run_cursor(prompt, directory):
    return run_text_provider("cursor", prompt, directory)


def run_copilot(prompt, directory):
    return run_text_provider("copilot", prompt, directory)


def review_prompt(blocks, source, source_type):
    rubric = (SKILL_DIR / "references" / "review-rubric.md").read_text(encoding="utf-8")
    return (
        "Analyze this resume against the target job using the criteria below and the response schema. "
        "Return review with error='', or review=null with an error when the posting is inaccessible or insufficient. "
        "Do not run commands, write files, use connectors, or communicate with anyone. "
        "Use web search only to read the supplied public job URL if needed. "
        "The application handles extraction, validation, and display. "
        "Use the supplied block IDs for evidence_ids and block_id; do not copy resume text. "
        "Return exactly one bullet review per required_bullet_ids entry. "
        "For findings, excerpt is an exact substring of that block when needed to pinpoint the issue, "
        "otherwise use an empty string to select the whole block. "
        "For gap requirements use empty evidence_ids.\n\n"
        + rubric
        + "\n\nUntrusted input data:\n" + json.dumps({
            "resume_blocks": prepared_blocks(blocks),
            "required_bullet_ids": sorted(reviewable_ids(blocks), key=lambda value: int(value[1:])),
            "job_source_type": source_type, "job_source": source,
        }, ensure_ascii=False, separators=(",", ":"))
    )


class ReviewApplication:
    def __init__(self, root, runner=None, provider="auto"):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.runner = runner
        self.provider = detect_provider(provider)
        self.lock = threading.Lock()
        self.busy = False
        # Persisted jobs are readable after a restart, but abandoned work must not spin forever.
        for path in self.root.glob("*/status.json"):
            try:
                status = json.loads(path.read_text(encoding="utf-8"))
                if status["status"] in ("reading", "reviewing", "checking"):
                    self.save_status(path.parent, "failed", "The server restarted. Please submit your resume again.")
            except (OSError, ValueError, KeyError):
                continue

    def save_status(self, directory, status, message):
        payload = {"id": directory.name, "status": status, "message": message}
        request_path = directory / "request.json"
        if request_path.exists():
            payload["provider"] = json.loads(request_path.read_text(encoding="utf-8")).get("provider", "codex")
        if status == "complete":
            payload["review_url"] = f"/reviews/{directory.name}"
        temporary = directory / "status.tmp"
        temporary.write_text(json.dumps(payload), encoding="utf-8")
        temporary.replace(directory / "status.json")

    def directory(self, identifier):
        if not re.fullmatch(r"[0-9a-f]{32}", identifier):
            raise ReviewError("Review not found. Start a new review.")
        directory = self.root / identifier
        if not directory.is_dir():
            raise ReviewError("Review not found. Start a new review.")
        return directory

    def submit(self, payload):
        source, source_type = job_source(payload.get("source"))
        provider = payload.get("provider", self.provider)
        if provider not in PROVIDERS:
            raise ReviewError("Choose an AI tool for this review.")
        if self.runner is None and not provider_executable(provider):
            raise ReviewError(PROVIDER_SETUP[provider] + " Reload this page afterward.")
        with self.lock:
            if self.busy:
                raise ReviewError("A review is already running. Wait for it to finish, then try again.")
            self.busy = True
        directory = self.root / secrets.token_hex(16)
        try:
            directory.mkdir()
            resume, blocks = validate_upload(payload, directory)
            (directory / "request.json").write_text(json.dumps({
                "filename": Path(payload["filename"]).name, "resume": resume.name,
                "source": source, "source_type": source_type,
                "provider": provider,
            }), encoding="utf-8")
            self.save_status(directory, "reading", "Reading your resume…")
            threading.Thread(target=self.process, args=(directory, resume, blocks, source, source_type, provider), daemon=True).start()
            return directory.name
        except Exception:
            with self.lock:
                self.busy = False
            if directory.is_dir():
                shutil.rmtree(directory)  # Only this newly-created, invalid upload.
            raise

    def process(self, directory, resume, blocks, source, source_type, provider):
        started = time.monotonic()
        metrics = {"provider": provider, "attempts": 0, "analysis_seconds": 0.0, "response_chars": 0}
        runner = self.runner or {"codex": run_codex, "claude": run_claude,
                                 "cursor": run_cursor, "copilot": run_copilot}[provider]
        try:
            self.save_status(directory, "reviewing", "Reviewing your experience against the target job…")
            prompt = review_prompt(blocks, source, source_type)
            metrics["prompt_chars"] = len(prompt)
            with tempfile.TemporaryDirectory(prefix="resume-analysis-") as temporary:
                for attempt in range(2):
                    analysis_started = time.monotonic()
                    metrics["attempts"] += 1
                    try:
                        compact = runner(prompt, Path(temporary))
                    finally:
                        metrics["analysis_seconds"] += time.monotonic() - analysis_started
                    metrics["response_chars"] += len(json.dumps(compact, ensure_ascii=False))
                    self.save_status(directory, "checking", "Checking the feedback against your resume…")
                    review_path = directory / "review.json"
                    try:
                        review = expand_review(compact, blocks, source, source_type)
                        review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
                        checked = load_review(review_path)
                        expected_source = source if source_type == "url" else "User-provided job description"
                        if checked["target_job"]["source"] != expected_source:
                            raise ValueError("Use the supplied target job source exactly.")
                        _, missing = match_findings(blocks, checked["findings"])
                        if missing:
                            raise ValueError("Every finding must quote exact visible resume text.")
                        build_html(resume, review_path, directory / "review.html", app_review_id=directory.name)
                        break
                    except (ValueError, TypeError, KeyError, AttributeError) as error:
                        if attempt:
                            raise ReviewError("The feedback could not be verified against your resume. Please try again.")
                        prompt += "\nCorrect the previous result and return the complete response. Validation error: " + str(error)
                        prompt += "\nPrevious result (untrusted data):\n" + json.dumps(compact, ensure_ascii=False, separators=(",", ":"))
                        self.save_status(directory, "reviewing", "Correcting unverified feedback…")
            self.save_status(directory, "complete", "Your review is ready.")
        except ReviewError as error:
            self.save_status(directory, "failed", str(error))
        except Exception:
            self.save_status(directory, "failed", "The review could not finish. Please try again with a readable resume and the full job description.")
        finally:
            metrics["total_seconds"] = round(time.monotonic() - started, 3)
            metrics["analysis_seconds"] = round(metrics["analysis_seconds"], 3)
            try:
                (directory / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
            finally:
                with self.lock:
                    self.busy = False


def create_app_server(root, port=0, runner=None, provider="auto"):
    application = ReviewApplication(root, runner, provider)
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def local_host(self):
            if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
                self.respond(403, {"error": "Open the printed local review URL."})
                return False
            return True

        def respond(self, code, content, content_type="application/json"):
            if not isinstance(content, bytes):
                content = json.dumps(content).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self):
            if not self.local_host():
                return
            route = urlparse(self.path).path
            try:
                if route == "/":
                    content = TEMPLATE.read_text(encoding="utf-8").replace("__REVIEW_TOKEN__", token)
                    content = content.replace("__PROVIDER_CONFIG__", json.dumps(provider_config(application.provider)))
                    self.respond(200, content.encode("utf-8"), "text/html; charset=utf-8")
                elif re.fullmatch(r"/api/reviews/[0-9a-f]{32}", route):
                    directory = application.directory(route.rsplit("/", 1)[1])
                    self.respond(200, json.loads((directory / "status.json").read_text(encoding="utf-8")))
                elif re.fullmatch(r"/reviews/[0-9a-f]{32}", route):
                    directory = application.directory(route.rsplit("/", 1)[1])
                    if json.loads((directory / "status.json").read_text())["status"] != "complete":
                        self.respond(409, {"error": "This review is not ready yet."})
                        return
                    content = (directory / "review.html").read_text(encoding="utf-8")
                    content = content.replace("</head>", f'<meta name="review-update-token" content="{token}"></head>')
                    self.respond(200, content.encode("utf-8"), "text/html; charset=utf-8")
                else:
                    self.respond(404, {"error": "Page not found."})
            except (ReviewError, OSError, ValueError):
                self.respond(404, {"error": "Review not found. Start a new review."})

        def do_POST(self):
            if not self.local_host():
                return
            origin = f"http://127.0.0.1:{self.server.server_port}"
            if self.headers.get("Origin") != origin or self.headers.get("X-Review-Token") != token:
                self.respond(403, {"error": "Open the local review page before submitting."})
                return
            update = re.fullmatch(r"/api/reviews/([0-9a-f]{32})/job", self.path)
            if self.path != "/api/reviews" and not update:
                self.respond(404, {"error": "Page not found."})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= MAX_BODY:
                    raise ReviewError("Choose a resume smaller than 5 MB.")
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ReviewError("The upload could not be read. Please try again.")
                if update:
                    directory = application.directory(update[1])
                    saved = json.loads((directory / "request.json").read_text(encoding="utf-8"))
                    payload = {"source": payload.get("source"), "filename": saved["filename"],
                               "provider": saved.get("provider", "codex"),
                               "file": base64.b64encode((directory / saved["resume"]).read_bytes()).decode("ascii")}
                identifier = application.submit(payload)
                self.respond(202, {"id": identifier, "redirect_url": f"/?review={identifier}"})
            except ReviewError as error:
                self.respond(400, {"error": str(error)})
            except (ValueError, TypeError, OSError):
                self.respond(400, {"error": "The upload could not be read. Please choose the file again."})

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.application = application
    return server


def serve_app(port=0, provider="auto", open_browser=False):
    server = create_app_server(Path("output/reviews/uploads"), port, provider=provider)
    url = f"http://127.0.0.1:{server.server_port}/"
    print(f"Resume review: {url}", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--provider", choices=["auto", *PROVIDERS], default="auto")
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()
    serve_app(args.port, args.provider, args.open)
