#!/usr/bin/env python3
"""Register the shared resume skills for local AI tools without directory symlinks."""

import argparse
import os
from pathlib import Path


PROJECT_FOLDERS = {
    "codex": ".agents",
    "claude": ".claude",
    "cursor": ".cursor",
    "copilot": ".github",
}
USER_FOLDERS = dict(PROJECT_FOLDERS, codex=".codex", copilot=".copilot")
SKILLS = ("resume-writing", "resume-review")
MARKER = "<!-- Managed by bin/register-skills.py. -->"


def entry_text(repo, host, name, scope):
    shared = repo / ".github" / "skills" / name
    frontmatter = (shared / "SKILL.md").read_text().split("---", 2)[1].strip()
    if scope == "project":
        target = f"../../../.github/skills/{name}/SKILL.md"
        location = "the shared skill directory linked above"
        interpreter = ".venv/bin/python"
        script = f".github/skills/{name}/scripts/render_review.py"
        working_directory = "the repository containing this entry file"
    else:
        target = str(shared / "SKILL.md")
        location = f"`{shared}`"
        interpreter = str(repo / ".venv" / "bin" / "python")
        script = str(shared / "scripts" / "render_review.py")
        working_directory = f"`{repo}`"
    text = (
        f"---\n{frontmatter}\n---\n\n{MARKER}\n\n# {name}\n\n"
        f"Read and follow the complete shared workflow at [{name}](<{target}>).\n\n"
        f"Resolve its scripts, references, and templates relative to {location}, "
        "rather than this launcher or the current workspace. "
        f"Prefer `{interpreter}` when available; otherwise use Python 3 with the required dependencies.\n"
    )
    if name == "resume-review":
        text += (
            f"\nThis launcher is for {host}. For a request to open Resume Review, "
            f"run from {working_directory}:\n\n```bash\n"
            f'"{interpreter}" "{script}" --provider {host}\n```\n\n'
            "Keep the server running and open its printed URL in the host browser panel, "
            "or add `--open` for the default browser. The user supplies the resume and job "
            "in that screen. Follow the shared chat workflow for direct analysis of supplied files. "
            "If this entry is read by another supported host, use that host's explicit provider "
            "as required by the shared skill; never substitute a provider silently.\n"
        )
    return text


def register(repo, home, host, scope):
    if scope == "project":
        root = repo / PROJECT_FOLDERS[host] / "skills"
    elif host == "codex" and os.environ.get("CODEX_HOME") and home == Path.home():
        root = Path(os.environ["CODEX_HOME"]) / "skills"
    else:
        root = home / USER_FOLDERS[host] / "skills"
    for name in SKILLS:
        folder = root / name
        shared = repo / ".github" / "skills" / name
        if folder == shared:
            print(f"Shared skill already registered: {shared / 'SKILL.md'}")
            continue
        if folder.is_symlink():
            if scope != "project" or folder.resolve() != shared:
                raise ValueError(f"Refusing to replace unrelated link: {folder}")
            # Replace only the known project link; retain the shared skill itself.
            folder.unlink()
            folder.mkdir()
        elif folder.exists() and not folder.is_dir():
            raise ValueError(f"Not a skill directory: {folder}")
        entry = folder / "SKILL.md"
        if entry.is_symlink():
            raise ValueError(f"Refusing to replace linked entry: {entry}")
        if entry.exists() and MARKER not in entry.read_text():
            print(f"Preserved existing entry: {entry}")
            continue
        folder.mkdir(parents=True, exist_ok=True)
        entry.write_text(entry_text(repo, host, name, scope))
        print(f"Registered: {entry}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=tuple(PROJECT_FOLDERS), nargs="+",
                        default=list(PROJECT_FOLDERS))
    parser.add_argument("--scope", choices=("user", "project"), default="user")
    parser.add_argument("--home", type=Path, default=Path.home(),
                        help="Home directory for personal registrations")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    for name in SKILLS:
        if not (repo / ".github" / "skills" / name / "SKILL.md").is_file():
            parser.error(f"Shared skill is missing: {name}")
    try:
        for host in args.host:
            register(repo, args.home.expanduser().resolve(), host, args.scope)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Registration failed: {error}\n")


if __name__ == "__main__":
    main()
