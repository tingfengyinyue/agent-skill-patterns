#!/usr/bin/env python3
"""Collect repository-history and static indicators that may signal Code Rot.

This is an indicator scanner, not a quality verdict. It intentionally avoids
language-specific dead-code or complexity claims that require a parser or the
repository's own tooling.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


SOURCE_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cs", ".go", ".java", ".js", ".jsx", ".kt",
    ".mjs", ".php", ".py", ".rb", ".rs", ".scala", ".swift", ".ts", ".tsx",
}
EXCLUDED_PARTS = {
    ".git", ".venv", "node_modules", "vendor", "dist", "build", "coverage",
    "__pycache__", ".next", "target", "generated", "gen",
}
MARKER_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE)


@dataclass
class FileSignal:
    path: str
    lines: int
    churn: int
    markers: int

    @property
    def hotspot_score(self) -> float:
        # This is a ranking signal only, not a health score.
        return round(self.churn * 2 + self.lines / 100 + self.markers * 3, 1)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout


def source_files(repo: Path) -> list[Path]:
    result: list[Path] = []
    for raw in git(repo, "ls-files", "-z").split("\0"):
        if not raw:
            continue
        path = Path(raw)
        if path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        result.append(path)
    return result


def change_counts(repo: Path, since_days: int, allowed: set[str]) -> Counter[str]:
    names = git(
        repo,
        "log",
        f"--since={since_days} days ago",
        "--name-only",
        "--format=",
        "--",
    )
    return Counter(name for name in names.splitlines() if name in allowed)


def read_signals(repo: Path, files: list[Path], churn: Counter[str]) -> list[FileSignal]:
    signals: list[FileSignal] = []
    for relative in files:
        absolute = repo / relative
        try:
            text = absolute.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
        markers = len(MARKER_RE.findall(text))
        file_churn = churn.get(relative.as_posix(), 0)
        if lines >= 300 or file_churn > 0 or markers > 0:
            signals.append(FileSignal(relative.as_posix(), lines, file_churn, markers))
    return signals


def render(repo: Path, since_days: int, signals: list[FileSignal], limit: int) -> str:
    ranked = sorted(signals, key=lambda item: item.hotspot_score, reverse=True)[:limit]
    marker_total = sum(item.markers for item in signals)
    churn_total = sum(item.churn for item in signals)
    large_files = sum(item.lines >= 500 for item in signals)

    rows = [
        "# Code Rot Indicator Report",
        "",
        f"Repository: {repo}",
        f"History window: last {since_days} days",
        "",
        "This report contains indicators and ranked candidates, not a verdict. "
        "Verify candidates with the repository graph, code, tests, and local rules.",
        "",
        "## Summary",
        "",
        f"- Candidate files: {len(signals)}",
        f"- Files at or above 500 lines: {large_files}",
        f"- Change events in the window: {churn_total}",
        f"- TODO/FIXME/HACK/XXX markers: {marker_total}",
        "",
        "## Ranked hotspots",
        "",
        "| File | Lines | Change events | Markers | Ranking signal |",
        "|---|---:|---:|---:|---:|",
    ]
    rows.extend(
        f"| {item.path} | {item.lines} | {item.churn} | {item.markers} | {item.hotspot_score} |"
        for item in ranked
    )
    rows.extend(
        [
            "",
            "## Interpretation prompts",
            "",
            "- Verify whether high churn reflects active development or repeated repair.",
            "- Check whether large files contain multiple responsibilities or stable generated code.",
            "- Search marker locations and determine whether they are planned work, stale debt, or harmless notes.",
            "- Use the code graph to test for unused symbols, duplicate implementations, and boundary drift.",
            "- Compare candidate files with their tests, owners, documentation, and runtime signals.",
        ]
    )
    return "\n".join(rows) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("--since-days", type=int, default=180)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    repo = args.repo.resolve()
    if not (repo / ".git").exists() and not (repo / ".git").is_file():
        raise SystemExit(f"not a git repository: {repo}")
    if args.since_days <= 0 or args.limit <= 0:
        raise SystemExit("since-days and limit must be positive")

    files = source_files(repo)
    allowed = {path.as_posix() for path in files}
    churn = change_counts(repo, args.since_days, allowed)
    signals = read_signals(repo, files, churn)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(repo, args.since_days, signals, args.limit), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
