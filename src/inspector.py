
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


class FunctionAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.defined: dict[str, int] = {}
        self.used: set[str] = set()

    def visit_FunctionDef(self, node):
        # Analyze nested functions independently.
        for arg in (
            node.args.posonlyargs
            + node.args.args
            + node.args.kwonlyargs
        ):
            self.defined[arg.arg] = arg.lineno if hasattr(arg, "lineno") else node.lineno

        if node.args.vararg:
            self.defined[node.args.vararg.arg] = node.lineno
        if node.args.kwarg:
            self.defined[node.args.kwarg.arg] = node.lineno

        for statement in node.body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
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


def _check_names(tree: ast.AST) -> list[Issue]:
    issues = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name
            if name.startswith("__") and name.endswith("__"):
                continue

            if isinstance(node, ast.ClassDef):
                valid = name[0].isupper() and "_" not in name
                expected = "PascalCase"
            else:
                valid = name.islower()
                expected = "lowercase_with_underscores"

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
        tokens = tokenize.tokenize(io.BytesIO(source.encode("utf-8")).readline)
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
