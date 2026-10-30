
import argparse
import json
import sys
from pathlib import Path

from py_code_inspector.inspector import inspect_file


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Python files for common code issues."
    )

    parser.add_argument("path", help="Python file or directory to inspect")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--output", help="Write the report to a file")
    parser.add_argument(
        "--select",
        help="Comma-separated issue codes to include, e.g. S001,W001",
    )
    parser.add_argument(
        "--severity",
        choices=["all", "warning", "error"],
        default="all",
        help="Filter issues by severity (default: all).",
    )

    args = parser.parse_args()
    target = Path(args.path)

    if not target.exists():
        print(f"Error: path does not exist: {target}", file=sys.stderr)
        return 2

    if target.is_file():
        files = [target] if target.suffix == ".py" else []
    else:
        files = sorted(target.rglob("*.py"))

    if not files:
        print("No Python files found.", file=sys.stderr)
        return 0

    selected_codes = None
    if args.select:
        selected_codes = {
            code.strip().upper()
            for code in args.select.split(",")
            if code.strip()
        }

    results = []
    issue_count = 0
    error_count = 0

    for file in files:
        issues = inspect_file(file)

        if selected_codes is not None:
            issues = [issue for issue in issues if issue.code in selected_codes]

        if args.severity != "all":
            issues = [
                issue for issue in issues
                if issue.severity == args.severity
            ]

        results.append(
            {
                "file": str(file),
                "issues": [
                    {
                        "code": issue.code,
                        "message": issue.message,
                        "line": issue.line,
                        "severity": issue.severity,
                    }
                    for issue in issues
                ],
            }
        )

        issue_count += len(issues)
        error_count += sum(issue.severity == "error" for issue in issues)

    if args.format == "json":
        report = json.dumps(results, indent=2, ensure_ascii=False)
    else:
        lines = []

        for result in results:
            lines.append(f"\n{result['file']}")

            if not result["issues"]:
                lines.append("  No issues found.")
                continue

            for issue in result["issues"]:
                lines.append(
                    f"  {issue['severity'].upper()} "
                    f"[{issue['code']}] line {issue['line']}: "
                    f"{issue['message']}"
                )

        lines.append(
            f"\nInspection complete. Files: {len(files)} | "
            f"Issues: {issue_count} | Errors: {error_count}"
        )
        report = "\n".join(lines)

    if args.output:
        try:
            Path(args.output).write_text(report + "\n", encoding="utf-8")
            print(f"Report saved to {args.output}")
        except OSError as error:
            print(f"Error: could not save report: {error}", file=sys.stderr)
            return 2
    else:
        print(report)

    return 1 if issue_count else 0


if __name__ == "__main__":
    raise SystemExit(main())

