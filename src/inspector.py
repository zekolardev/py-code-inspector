
import ast
import io
import re
import tokenize
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Issue:
    code: str
    message: str
    line: int
    severity: str = "warning"


class FunctionAnalyzer(ast.NodeVisitor):
    """Analyze local variable assignments within one function."""

    def __init__(self):
        self.defined: dict[str, int] = {}
        self.used: set[str] = set()

    def visit_FunctionDef(self, node):
        for statement in node.body:
            if isinstance(
                statement,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            ):
                if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.defined[statement.name] = statement.lineno
                continue

            self.visit(statement)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, node):
        return

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.defined[node.id] = node.lineno
        elif isinstance(node.ctx, ast.Load):
            self.used.add(node.id)

    def visit_ExceptHandler(self, node):
        if node.name:
            self.defined[node.name] = node.lineno

        if node.type:
            self.visit(node.type)

        for statement in node.body:
            self.visit(statement)


def _check_names(tree: ast.AST) -> list[Issue]:
    issues = []
    snake_case_pattern = re.compile(r"^[a-z_][a-z0-9_]*$")

    for node in ast.walk(tree):
        if not isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            continue

        name = node.name

        if name.startswith("__") and name.endswith("__"):
            continue

        if isinstance(node, ast.ClassDef):
            valid = (
                name.isidentifier()
                and name[0].isupper()
                and "_" not in name
            )
            expected = "PascalCase"
        else:
            valid = bool(snake_case_pattern.fullmatch(name))
            expected = "snake_case"

        if not valid:
            issues.append(
                Issue(
                    code="S001",
                    message=f"Use {expected} for '{name}'.",
                    line=node.lineno,
                )
            )

    return issues


def _check_unused_variables(tree: ast.AST) -> list[Issue]:
    issues = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        analyzer = FunctionAnalyzer()
        analyzer.visit(node)

        for name, line in analyzer.defined.items():
            if name not in analyzer.used and not name.startswith("_"):
                issues.append(
                    Issue(
                        code="W001",
                        message=f"'{name}' is assigned but never used.",
                        line=line,
                    )
                )

    return issues


def inspect_code(source: str) -> list[Issue]:
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return [
            Issue(
                code="E001",
                message=f"Syntax error: {error.msg}",
                line=error.lineno or 1,
                severity="error",
            )
        ]

    issues = _check_names(tree)
    issues.extend(_check_unused_variables(tree))

    try:
        tokens = tokenize.tokenize(
            io.BytesIO(source.encode("utf-8")).readline
        )

        for token in tokens:
            if token.type == tokenize.COMMENT and len(token.string) > 88:
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
