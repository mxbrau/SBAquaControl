#!/usr/bin/env python3
"""
Create the GitHub issues described by .github/issues/*.md.

Each file carries front matter:

    ---
    title: <issue title>
    labels: bug, firmware          # optional, comma separated
    milestone: <milestone title>   # optional
    ---
    <body>

The script is idempotent: an issue whose title already exists (open or closed) is
skipped, so it is safe to re-run after editing the bodies. Labels are created if
they are missing.

Usage:
    gh auth login                                    # once
    uv run python .github/scripts/create_issues.py --dry-run
    uv run python .github/scripts/create_issues.py
    uv run python .github/scripts/create_issues.py --repo mxbrau/SBAquaControl
"""

import argparse
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
ISSUE_DIR = os.path.join(REPO_ROOT, ".github", "issues")

# label -> (colour, description)
LABELS = {
    "bug": ("d73a4a", "Something isn't working"),
    "enhancement": ("a2eeef", "New feature or request"),
    "firmware": ("1d76db", "C/C++ firmware on the ESP8266"),
    "ui": ("0e8a16", "Web interface on the SD card"),
    "performance": ("fbca04", "Slower than it should be"),
    "docs": ("0075ca", "Documentation"),
    "testing": ("5319e7", "Test coverage and tooling"),
    "tooling": ("c5def5", "Dev environment, build, scripts"),
    "network": ("bfd4f2", "WiFi / connectivity"),
    "needs-hardware": ("d4c5f9", "Cannot be verified without the device"),
}


def gh(args, check=True, capture=True):
    return subprocess.run(
        ["gh"] + args,
        cwd=REPO_ROOT,
        capture_output=capture,
        text=True,
        check=check,
    )


def parse_issue(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    if not lines or lines[0].strip() != "---":
        raise SystemExit(f"{path}: missing front matter")

    meta, body_start = {}, None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            body_start = i + 1
            break
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()

    if body_start is None:
        raise SystemExit(f"{path}: unterminated front matter")
    if "title" not in meta:
        raise SystemExit(f"{path}: front matter needs a title")

    body = "\n".join(lines[body_start:]).strip() + "\n"
    labels = [l.strip() for l in meta.get("labels", "").split(",") if l.strip()]
    return meta["title"], labels, meta.get("milestone", ""), body


def detect_repo():
    try:
        result = gh(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def ensure_labels(repo, labels, dry_run):
    for label in labels:
        colour, description = LABELS.get(label, ("ededed", ""))
        cmd = [
            "label", "create", label,
            "--color", colour,
            "--description", description,
            "--repo", repo,
            "--force",  # update colour/description if it already exists
        ]
        if dry_run:
            print(f"  would ensure label: {label} ({colour})")
            continue
        gh(cmd, check=False)
        print(f"  label ready: {label}")


def existing_titles():
    """All issue titles in the repo, open and closed."""
    result = gh(
        ["issue", "list", "--state", "all", "--limit", "500", "--json", "title",
         "-q", ".[].title"]
    )
    return {t.strip() for t in result.stdout.splitlines() if t.strip()}


def create_issue(repo, title, labels, milestone, body, dry_run):
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(body)
        body_file = f.name
    try:
        cmd = ["issue", "create", "--repo", repo, "--title", title,
               "--body-file", body_file]
        if labels:
            cmd += ["--label", ",".join(labels)]
        if milestone:
            cmd += ["--milestone", milestone]
        if dry_run:
            print(f"  would create: {title}")
            print(f"                labels: {', '.join(labels) or '-'} "
                  f"milestone: {milestone or '-'} body: {len(body.splitlines())} lines")
            return None
        result = gh(cmd)
        print(f"  created: {result.stdout.strip()}")
        return result.stdout.strip()
    finally:
        os.remove(body_file)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print actions, change nothing")
    parser.add_argument("--repo", help="owner/name (default: the current repo's remote)")
    args = parser.parse_args()

    files = sorted(f for f in os.listdir(ISSUE_DIR) if f.endswith(".md"))
    if not files:
        raise SystemExit(f"no issue files in {ISSUE_DIR}")

    repo = args.repo or detect_repo()
    if not repo:
        raise SystemExit("could not determine the repository - pass --repo owner/name")

    print(f"Repository: {repo}")
    print(f"Issue files: {len(files)} in {ISSUE_DIR}")

    known = existing_titles()
    print(f"Existing issues: {len(known)}")

    created = skipped = 0
    for name in files:
        title, labels, milestone, body = parse_issue(os.path.join(ISSUE_DIR, name))
        print(f"\n{name}")
        print(f"  title: {title}")
        if title in known:
            print("  SKIP: an issue with this title already exists")
            skipped += 1
            continue
        ensure_labels(repo, labels, args.dry_run)
        create_issue(repo, title, labels, milestone, body, args.dry_run)
        created += 1

    print(f"\n{created} created, {skipped} skipped"
          + (" (dry run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
