
import ast
import io
import tokenize
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Issue:
    code: str
    message: str
    line: int
    severity: str = "warning"


def inspect_code(source: str) -> list[Issue]:
    issues: list[Issue] = []

    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        issues.append(
            Issue(
                code="E001",
                message=f"Syntax error: {error.msg}",
                line=error.lineno or 1,
                severity="error",
            )
        )
        return issues

    defined_names: dict[str, int] = {}
    used_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name.startswith("_") and not node.name.startswith("__"):
                pass
            elif node.name and not node.name.islower():
                issues.append(
                    Issue(
                        code="S001",
                        message=f"Use lowercase_with_underscores for '{node.name}'.",
                        line=node.lineno,
                    )
                )

        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Store):
                defined_names[node.id] = node.lineno
            elif isinstance(node.ctx, ast.Load):
                used_names.add(node.id)

    for name, line in defined_names.items():
        if name not in used_names and not name.startswith("_"):
            issues.append(
                Issue(
                    code="W001",
                    message=f"'{name}' is assigned but never used.",
                    line=line,
                )
            )

    try:
        tokens = tokenize.tokenize(io.BytesIO(source.encode("utf-8")).readline)
        for token in tokens:
            if token.type == tokenize.COMMENT:
                if len(token.string) > 88:
                    issues.append(
                        Issue(
                            code="S002",
                            message="Comment is longer than 88 characters.",
                            line=token.start[0],
                        )
                    )
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass

    return sorted(issues, key=lambda issue: (issue.line, issue.code))


def inspect_file(file_path: str | Path) -> list[Issue]:
    path = Path(file_path)

    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return [
            Issue(
                code="E002",
                message=f"Cannot read file: {error}",
                line=1,
                severity="error",
            )
        ]

    return inspect_code(source)
