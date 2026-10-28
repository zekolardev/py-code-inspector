
import argparse
from pathlib import Path

from src.inspector import inspect_file


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Python files for common code issues."
    )
    parser.add_argument("path", help="Python file or directory to inspect")
    args = parser.parse_args()

    target = Path(args.path)

    if not target.exists():
        print(f"Error: path does not exist: {target}")
        return 2

    files = [target] if target.is_file() else sorted(target.rglob("*.py"))
    files = [file for file in files if file.suffix == ".py"]

    if not files:
        print("No Python files found.")
        return 0

    issue_count = 0

    for file in files:
        issues = inspect_file(file)
        print(f"\n{file}")

        if not issues:
            print("  No issues found.")
            continue

        for issue in issues:
            print(
                f"  {issue.severity.upper()} "
                f"[{issue.code}] line {issue.line}: {issue.message}"
            )
            issue_count += 1

    print(f"\nInspection complete. Issues found: {issue_count}")
    return 1 if issue_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
