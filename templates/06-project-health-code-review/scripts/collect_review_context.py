#!/usr/bin/env python3
"""Collect a deterministic, read-only first-pass context bundle for a repository review."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


RULE_FILES = {
    "AGENTS.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "pyproject.toml",
    "package.json",
    "go.mod",
    "Makefile",
    "Dockerfile",
    ".gitlab-ci.yml",
}


def run(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"[command failed: git {' '.join(args)}]\n{result.stderr.strip()}"
    return result.stdout.strip()


def discover_files(repo: Path) -> list[str]:
    tracked = run(repo, "ls-files").splitlines()
    selected: list[str] = []
    for item in tracked:
        name = Path(item).name
        if name in RULE_FILES or item.startswith(".github/workflows/"):
            selected.append(item)
    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("base", help="git ref used as the review fixed point")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--diff-context", type=int, default=20)
    args = parser.parse_args()

    repo = args.repo.resolve()
    output = args.output.resolve()
    if not (repo / ".git").exists() and not (repo / ".git").is_file():
        raise SystemExit(f"not a git repository: {repo}")

    base_sha = run(repo, "rev-parse", args.base)
    head_sha = run(repo, "rev-parse", "HEAD")
    if base_sha.startswith("[command failed"):
        raise SystemExit(base_sha)

    files = discover_files(repo)
    sections = [
        "# Project Review Context",
        "",
        f"- Repository: {repo}",
        f"- Base: {args.base} ({base_sha})",
        f"- HEAD: {head_sha}",
        "- Working tree:",
        "",
        "~~~text",
        run(repo, "status", "--short", "--branch"),
        "~~~",
        "## Commits",
        "~~~text",
        run(repo, "log", "--oneline", f"{args.base}..HEAD"),
        "~~~",
        "## Changed files",
        "~~~text",
        run(repo, "diff", "--name-status", f"{args.base}...HEAD"),
        "~~~",
        "## Diff statistics",
        "~~~text",
        run(repo, "diff", "--stat", f"{args.base}...HEAD"),
        "~~~",
        "## Repository context files",
    ]
    sections.extend(f"- {item}" for item in files)
    sections.extend(
        [
            "",
            "## Diff with enclosing context",
            "~~~diff",
            run(repo, "diff", f"--unified={args.diff_context}", f"{args.base}...HEAD"),
            "~~~",
            "",
            "## Review limitations",
            "This bundle is evidence for review, not a verdict. Read the listed context files, inspect callers/callees, and run relevant checks before making claims.",
        ]
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(sections) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
