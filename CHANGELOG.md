# Changelog

All notable changes to this project are documented in this file.

## [0.2.0] - Unreleased

### Added
- Module-level naming convention checks.
- Detection of bare except statements.
- Detection of unused module-level variables.
- Improved scope-aware local variable analysis.
- JSON report generation.
- Issue code and severity filtering.
- Automated GitHub Actions testing.

### Improved
- CLI error handling and exit codes.
- Python source inspection.
- Test coverage for scope analysis and exception handling.
- Project documentation.

### Fixed
- Variable scope analysis issues.
- Detection of variables referenced by nested functions.
- Handling of global and nonlocal declarations.