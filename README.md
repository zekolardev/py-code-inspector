
# Py Code Inspector

A lightweight Python code inspection tool that detects common code quality issues using Python's built-in libraries.

## Features

- Detects syntax errors
- Checks function and class naming conventions
- Identifies potentially unused variables
- Detects comments longer than 88 characters
- Inspects individual Python files or entire directories
- Supports readable text and JSON reports
- Filters issues by issue code or severity
- Saves inspection reports to a file
- Includes automated tests and GitHub Actions CI

## Requirements

- Python 3.14 or compatible version
- No third-party Python packages required

## Getting Started

Clone the repository:

```bash
git clone https://github.com/zekolardev/py-code-inspector.git
cd py-code-inspector
```

## Usage

Inspect a Python file:

```bash
python -m src.cli examples/sample.py
```

Inspect all Python files in a directory:

```bash
python -m src.cli examples
```

Generate a JSON report:

```bash
python -m src.cli examples --format json
```

Save the report to a file:

```bash
python -m src.cli examples --format json --output report.json
```

Filter by issue codes:

```bash
python -m src.cli examples --select S001,W001
```

Show only warnings:

```bash
python -m src.cli examples --severity warning
```

Show only errors:

```bash
python -m src.cli examples --severity error
```

## Issue Codes

| Code | Description |
| --- | --- |
| `E001` | Python syntax error |
| `E002` | File reading error |
| `S001` | Naming convention issue |
| `S002` | Comment longer than 88 characters |
| `W001` | Potentially unused variable |

## Running Tests

Run the automated test suite:

```bash
python -m unittest discover -v
```

The project includes tests for code inspection, CLI behavior, JSON output, and filtering options.

## Project Structure

```text
py-code-inspector/
├── .github/
│   └── workflows/
│       └── ci.yml
├── examples/
├── src/
│   ├── cli.py
│   └── inspector.py
├── tests/
│   ├── test_cli.py
│   └── test_inspector.py
├── .gitignore
└── README.md
```

## Continuous Integration

GitHub Actions runs the automated tests when changes are pushed to the `main` branch or a pull request targets `main`.

## Current Limitations

This is an early-stage project. Some checks are intentionally lightweight and may produce false positives. Additional rules and more advanced analysis can be introduced in future releases.

## License

No license has been specified yet.
