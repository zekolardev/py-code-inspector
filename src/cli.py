
import argparse
import json
from pathlib import Path

from src.inspector import inspect_file


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
    args = parser.parse_args()

    target = Path(args.path)

    if not target.exists():
        print(f"Error: path does not exist: {target}")
        return 2

    if target.is_file():
        files = [target] if target.suffix == ".py" else []
    else:
        files = sorted(target.rglob("*.py"))

    if not files:
        print("No Python files found.")
        return 0

    results = []
    issue_count = 0
    error_count = 0

    for file in files:
        issues = inspect_file(file)
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
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for result in results:
            print(f"\n{result['file']}")

            if not result["issues"]:
                print("  No issues found.")
                continue

            for issue in result["issues"]:
                print(
                    f"  {issue['severity'].upper()} "
                    f"[{issue['code']}] line {issue['line']}: "
                    f"{issue['message']}"
                )

        print(
            f"\nInspection complete. Files: {len(files)} | "
            f"Issues: {issue_count} | Errors: {error_count}"
        )

    return 1 if issue_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
