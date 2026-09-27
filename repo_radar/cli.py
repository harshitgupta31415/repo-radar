from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audit import AuditResult, audit_repository


def _text_report(result: AuditResult) -> str:
    lines = [
        f"Repo Radar — {result.path}",
        f"Score: {result.score}/{result.maximum_score} ({result.percentage}%)",
        "",
    ]
    for check in result.checks:
        marker = "PASS" if check.passed else "MISS"
        lines.append(f"[{marker}] {check.title} — {check.detail}")
        if check.suggestion:
            lines.append(f"       Fix: {check.suggestion}")
    return "\n".join(lines)


def _markdown_report(result: AuditResult) -> str:
    lines = [
        "# Repo Radar report",
        "",
        f"**Score:** {result.score}/{result.maximum_score} ({result.percentage}%)",
        "",
        "| Check | Result | Detail |",
        "| --- | --- | --- |",
    ]
    for check in result.checks:
        status = "Pass" if check.passed else "Needs work"
        detail = check.detail.replace("|", "\\|")
        lines.append(f"| {check.title} | {status} | {detail} |")
    suggestions = [check for check in result.checks if check.suggestion]
    if suggestions:
        lines.extend(["", "## Suggested next steps", ""])
        lines.extend(f"- **{check.title}:** {check.suggestion}" for check in suggestions)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit repository health and share an actionable score.")
    parser.add_argument("path", nargs="?", default=".", help="Repository directory (default: current directory)")
    parser.add_argument("--format", choices=("text", "json", "markdown"), default="text")
    parser.add_argument("--output", type=Path, help="Write the report to a file")
    parser.add_argument("--fail-under", type=int, default=0, metavar="PERCENT")
    parser.add_argument("--max-file-kb", type=int, default=1024)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not 0 <= args.fail_under <= 100:
        raise SystemExit("--fail-under must be between 0 and 100")
    try:
        result = audit_repository(args.path, args.max_file_kb)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    if args.format == "json":
        report = json.dumps(result.to_dict(), indent=2)
    elif args.format == "markdown":
        report = _markdown_report(result)
    else:
        report = _text_report(result)

    if args.output:
        args.output.write_text(report + "\n", encoding="utf-8")
        print(f"Wrote report to {args.output}")
    else:
        print(report)
    return 1 if result.percentage < args.fail_under else 0


if __name__ == "__main__":
    raise SystemExit(main())
