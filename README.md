# Py Code Inspector

A lightweight, dependency-free static analysis tool for Python source code.

Py Code Inspector analyzes Python files and directories to identify common code quality issues using Python's built-in AST and other standard library modules.

## Features

- Detects Python syntax errors.
- Checks function and class naming conventions.
- Identifies potentially unused local variables and parameters.
- Identifies potentially unused module-level variables.
- Checks module-level variable naming conventions.
- Detects comments longer than 120 characters.
- Reports bare `except:` statements.
- Inspects individual Python files or entire directories recursively.
- Supports text and JSON output formats.
- Filters findings by issue code or severity.
- Saves reports to external files.
- Includes automated unit tests and GitHub Actions CI.

## Requirements

- Python 3.14 or newer.
- No runtime third-party dependencies.

## Installation

Clone the repository:

```bash
git clone https://github.com/zekolardev/py-code-inspector.git
cd py-code-inspector