#!/usr/bin/env python3
"""
Parse and summarize Semgrep JSON output.

Examples:
  python parse_semgrep_baseline.py ../semgrep-baseline.json
  python parse_semgrep_baseline.py ../semgrep-baseline.json --min-severity WARNING
  python parse_semgrep_baseline.py ../semgrep-baseline.json --format json --output summary.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SEVERITY_ORDER = {
    "UNKNOWN": 0,
    "INFO": 1,
    "WARNING": 2,
    "ERROR": 3,
}

SEVERITY_ALIASES = {
    "LOW": "INFO",
    "MEDIUM": "WARNING",
    "HIGH": "ERROR",
    "CRITICAL": "ERROR",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize Semgrep JSON findings.")
    parser.add_argument(
        "input",
        nargs="?",
        default="semgrep-baseline.json",
        help="Path to Semgrep JSON output (default: semgrep-baseline.json).",
    )
    parser.add_argument(
        "--min-severity",
        choices=["INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Only include findings at or above this severity.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )
    parser.add_argument(
        "--output",
        default="-",
        help="Output file path. Use '-' for stdout (default).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="How many top rules/files to include in summary.",
    )
    parser.add_argument(
        "--max-message-length",
        type=int,
        default=140,
        help="Truncate message length in text output.",
    )
    parser.add_argument(
        "--no-dedupe",
        action="store_true",
        help="Disable de-duplication.",
    )
    parser.add_argument(
        "--include-path-regex",
        action="append",
        default=[],
        help="Include only findings whose path matches this regex. Can be used multiple times.",
    )
    parser.add_argument(
        "--exclude-path-regex",
        action="append",
        default=[],
        help="Exclude findings whose path matches this regex. Can be used multiple times.",
    )
    parser.add_argument(
        "--include-rule-regex",
        action="append",
        default=[],
        help="Include only findings whose check_id matches this regex. Can be used multiple times.",
    )
    parser.add_argument(
        "--exclude-rule-regex",
        action="append",
        default=[],
        help="Exclude findings whose check_id matches this regex. Can be used multiple times.",
    )
    parser.add_argument(
        "--exclude-third-party",
        action="store_true",
        help="Exclude common third-party/library paths and minified assets.",
    )
    return parser.parse_args()


def normalize_severity(value: Any) -> str:
    if value is None:
        return "UNKNOWN"
    text = str(value).strip().upper()
    if text in SEVERITY_ORDER:
        return text
    return SEVERITY_ALIASES.get(text, "UNKNOWN")


def flatten_finding(item: dict[str, Any]) -> dict[str, Any]:
    extra = item.get("extra", {}) or {}
    start = item.get("start", {}) or {}
    end = item.get("end", {}) or {}
    metadata = extra.get("metadata", {}) or {}

    cwe = metadata.get("cwe")
    if isinstance(cwe, list):
        cwe_value = ", ".join(str(x) for x in cwe)
    elif cwe is None:
        cwe_value = ""
    else:
        cwe_value = str(cwe)

    return {
        "severity": normalize_severity(extra.get("severity") or item.get("severity")),
        "check_id": str(item.get("check_id", "<unknown>")),
        "path": str(item.get("path", "<unknown>")),
        "start_line": int(start.get("line", 0) or 0),
        "end_line": int(end.get("line", 0) or 0),
        "message": str(extra.get("message", "")).strip(),
        "cwe": cwe_value,
    }


def severity_rank(severity: str) -> int:
    return SEVERITY_ORDER.get(severity, SEVERITY_ORDER["UNKNOWN"])


def dedupe_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    result: list[dict[str, Any]] = []
    for item in findings:
        key = (
            item["severity"],
            item["check_id"],
            item["path"],
            item["start_line"],
            item["end_line"],
            item["message"],
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def sort_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        findings,
        key=lambda x: (
            -severity_rank(x["severity"]),
            x["path"],
            x["start_line"],
            x["check_id"],
        ),
    )


def compile_patterns(patterns: list[str], label: str) -> list[re.Pattern[str]]:
    compiled: list[re.Pattern[str]] = []
    for pattern in patterns:
        try:
            compiled.append(re.compile(pattern))
        except re.error as exc:
            raise ValueError(f"Invalid {label} regex '{pattern}': {exc}") from exc
    return compiled


def matches_any(text: str, patterns: list[re.Pattern[str]]) -> bool:
    return any(p.search(text) for p in patterns)


def apply_filters(
    findings: list[dict[str, Any]],
    include_path_patterns: list[re.Pattern[str]],
    exclude_path_patterns: list[re.Pattern[str]],
    include_rule_patterns: list[re.Pattern[str]],
    exclude_rule_patterns: list[re.Pattern[str]],
) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for item in findings:
        path = item["path"]
        rule = item["check_id"]

        if include_path_patterns and not matches_any(path, include_path_patterns):
            continue
        if exclude_path_patterns and matches_any(path, exclude_path_patterns):
            continue
        if include_rule_patterns and not matches_any(rule, include_rule_patterns):
            continue
        if exclude_rule_patterns and matches_any(rule, exclude_rule_patterns):
            continue

        filtered.append(item)
    return filtered


def truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def build_summary(
    input_path: Path,
    total_raw: int,
    total_filtered: int,
    findings: list[dict[str, Any]],
    top_n: int,
) -> dict[str, Any]:
    sev_counter = Counter(item["severity"] for item in findings)
    rule_counter = Counter(item["check_id"] for item in findings)
    file_counter = Counter(item["path"] for item in findings)

    return {
        "input": str(input_path),
        "total_raw": total_raw,
        "total_filtered": total_filtered,
        "total_after_dedupe": len(findings),
        "severity_counts": dict(sorted(sev_counter.items(), key=lambda kv: -severity_rank(kv[0]))),
        "top_rules": [{"rule": k, "count": v} for k, v in rule_counter.most_common(top_n)],
        "top_files": [{"path": k, "count": v} for k, v in file_counter.most_common(top_n)],
    }


def render_text(summary: dict[str, Any], findings: list[dict[str, Any]], max_message_len: int) -> str:
    lines: list[str] = []
    lines.append("Semgrep Summary")
    lines.append(f"Input: {summary['input']}")
    lines.append(
        "Findings: raw={raw}, filtered={filtered}, deduped={deduped}".format(
            raw=summary["total_raw"],
            filtered=summary["total_filtered"],
            deduped=summary["total_after_dedupe"],
        )
    )

    severity_counts = summary["severity_counts"]
    if severity_counts:
        sev_text = " | ".join(
            f"{sev}:{count}" for sev, count in severity_counts.items()
        )
    else:
        sev_text = "None"
    lines.append(f"Severity: {sev_text}")
    lines.append("")

    lines.append("Top Rules:")
    if summary["top_rules"]:
        for idx, item in enumerate(summary["top_rules"], start=1):
            lines.append(f"{idx}. {item['rule']} ({item['count']})")
    else:
        lines.append("0. None")
    lines.append("")

    lines.append("Top Files:")
    if summary["top_files"]:
        for idx, item in enumerate(summary["top_files"], start=1):
            lines.append(f"{idx}. {item['path']} ({item['count']})")
    else:
        lines.append("0. None")
    lines.append("")

    lines.append("Findings:")
    if findings:
        for idx, item in enumerate(findings, start=1):
            location = f"{item['path']}:{item['start_line']}"
            msg = truncate(item["message"], max_message_len)
            lines.append(
                f"{idx}. [{item['severity']}] {location} {item['check_id']} - {msg}"
            )
    else:
        lines.append("0. None")
    return "\n".join(lines)


def infer_scan_root(findings: list[dict[str, Any]]) -> str | None:
    abs_paths = [item["path"] for item in findings if os.path.isabs(item["path"])]
    if not abs_paths:
        return None
    try:
        scan_root = os.path.commonpath(abs_paths)
    except ValueError:
        return None
    if scan_root and any(p == scan_root for p in abs_paths):
        scan_root = os.path.dirname(scan_root) or scan_root
    return scan_root


def render_json(_summary: dict[str, Any], findings: list[dict[str, Any]], scan_root: str | None) -> str:

    compact_findings: list[dict[str, Any]] = []
    for idx, item in enumerate(findings, start=1):
        path = item["path"]
        if scan_root and os.path.isabs(path):
            try:
                path = os.path.relpath(path, scan_root)
            except ValueError:
                pass
        path = path.replace("\\", "/")

        compact: dict[str, Any] = {
            "finding_id": f"SG-{idx:03d}",
            "severity": item["severity"],
            "check_id": item["check_id"],
            "path": path,
            "start_line": item["start_line"],
            "end_line": item["end_line"],
        }
        if item["cwe"]:
            compact["cwe"] = item["cwe"]
        if item["message"]:
            compact["message"] = item["message"]
        compact_findings.append(compact)

    payload = {"findings": compact_findings}
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)

    try:
        with input_path.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
    except FileNotFoundError:
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON in {input_path}: {exc}", file=sys.stderr)
        return 1

    results = data.get("results")
    if not isinstance(results, list):
        print("Invalid Semgrep JSON: expected top-level 'results' list.", file=sys.stderr)
        return 1

    raw_findings = [flatten_finding(item) for item in results if isinstance(item, dict)]
    total_raw = len(raw_findings)

    min_rank = severity_rank(args.min_severity)
    severity_filtered_findings = [
        item for item in raw_findings if severity_rank(item["severity"]) >= min_rank
    ]

    include_path_regexes = list(args.include_path_regex)
    exclude_path_regexes = list(args.exclude_path_regex)
    include_rule_regexes = list(args.include_rule_regex)
    exclude_rule_regexes = list(args.exclude_rule_regex)

    if args.exclude_third_party:
        exclude_path_regexes.extend(
            [
                r"/node_modules/",
                r"/vendor/",
                r"/third[-_]party/",
                r"/static/plugins/",
                r"/dist/",
                r"/build/",
                r"\.min\.(js|css)$",
            ]
        )

    try:
        include_path_patterns = compile_patterns(include_path_regexes, "include-path")
        exclude_path_patterns = compile_patterns(exclude_path_regexes, "exclude-path")
        include_rule_patterns = compile_patterns(include_rule_regexes, "include-rule")
        exclude_rule_patterns = compile_patterns(exclude_rule_regexes, "exclude-rule")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    filtered_findings = apply_filters(
        severity_filtered_findings,
        include_path_patterns,
        exclude_path_patterns,
        include_rule_patterns,
        exclude_rule_patterns,
    )
    total_filtered = len(filtered_findings)

    findings = filtered_findings if args.no_dedupe else dedupe_findings(filtered_findings)
    findings = sort_findings(findings)

    summary = build_summary(
        input_path=input_path,
        total_raw=total_raw,
        total_filtered=total_filtered,
        findings=findings,
        top_n=max(1, args.top),
    )

    detailed_findings = findings

    if args.format == "json":
        rendered = render_json(summary, detailed_findings, infer_scan_root(findings))
    else:
        rendered = render_text(summary, detailed_findings, args.max_message_length)

    if args.output == "-":
        print(rendered)
    else:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
