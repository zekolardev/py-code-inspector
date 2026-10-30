# Py Code Inspector

A lightweight, dependency-free Python static code inspection tool.

Py Code Inspector analyzes Python source files and directories to identify common code quality issues using Python's built-in libraries.

## Features

- Detects Python syntax errors.
- Checks function and class naming conventions.
- Identifies potentially unused local and module-level variables.
- Checks module-level variable naming conventions.
- Detects comments longer than 120 characters.
- Reports bare `except:` statements.
- Inspects individual Python files or entire directories.
- Supports text and JSON reports.
- Filters findings by issue code or severity.
- Saves reports to files.
- Includes automated tests and GitHub Actions CI.

## Requirements

- Python 3.14
- No third-party packages required.

## Installation

Clone the repository:

```bash
git clone https://github.com/zekolardev/py-code-inspector.git
cd py-code-inspector