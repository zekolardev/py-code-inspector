
import ast
import re
from dataclasses import dataclass


@dataclass
class Issue:
    code: str
    message: str
    line: int
    severity: str = "warning"


class FunctionAnalyzer(ast.NodeVisitor):
    """Detect local variables that are assigned but never used."""

    def __init__(self):
        self.issues = []

    def visit_FunctionDef(self, node):
        self._analyze_function(node)

    def visit_AsyncFunctionDef(self, node):
        self._analyze_function(node)

    def _analyze_function(self, node):
        assigned = {}
        used = set()
        nested_functions = []

        def collect(scope_node):
            for child in ast.iter_child_nodes(scope_node):
                if isinstance(
                    child,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                        ast.Lambda,
                        ast.ClassDef,
                    ),
                ):
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        nested_functions.append(child)
                    continue

                if isinstance(child, ast.Name):
                    if isinstance(child.ctx, ast.Store):
                        assigned.setdefault(child.id, child.lineno)
                    elif isinstance(child.ctx, ast.Load):
                        used.add(child.id)

                collect(child)

        for statement in node.body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                nested_functions.append(statement)
                continue

            collect(statement)

        # Count references inside nested functions for the enclosing scope.
        for nested in nested_functions:
            for item in ast.walk(nested):
                if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load):
                    used.add(item.id)

        # Function parameters are not unused local assignments.
        arguments = (
            node.args.posonlyargs
            + node.args.args
            + node.args.kwonlyargs
        )

        for argument in arguments:
            assigned.pop(argument.arg, None)

        if node.args.vararg:
            assigned.pop(node.args.vararg.arg, None)

        if node.args.kwarg:
            assigned.pop(node.args.kwarg.arg, None)

        for name, line in assigned.items():
            if name not in used and not name.startswith("_"):
                self.issues.append(
                    Issue(
                        code="W001",
                        message=f"Unused variable '{name}'.",
                        line=line,
                        severity="warning",
                    )
                )

        # Analyze nested functions independently.
        for nested in nested_functions:
            self._analyze_function(nested)


def _check_names(tree):
    issues = []
    snake_case_pattern = re.compile(r"^[a-z_][a-z0-9_]*$")

    for node in ast.walk(tree):
        if not isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            continue

        name = node.name

        # Special Python methods such as __init__ are exempt.
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
                    severity="warning",
                )
            )

    return issues


def _check_unused_variables(tree):
    analyzer = FunctionAnalyzer()
    analyzer.visit(tree)
    return analyzer.issues


def _check_long_comments(source):
    issues = []

    for line_number, line in enumerate(source.splitlines(), start=1):
        stripped = line.lstrip()

        if stripped.startswith("#") and len(stripped) > 120:
            issues.append(
                Issue(
                    code="S002",
                    message="Comment is longer than 120 characters.",
                    line=line_number,
                    severity="warning",
                )
            )

    return issues


def inspect_code(source):
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

    issues = []
    issues.extend(_check_names(tree))
    issues.extend(_check_unused_variables(tree))
    issues.extend(_check_long_comments(source))

    return sorted(issues, key=lambda issue: (issue.line, issue.code))


def inspect_file(path):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return inspect_code(file.read())
    except OSError as error:
        return [
            Issue(
                code="E002",
                message=f"Could not read file: {error}",
                line=1,
                severity="error",
            )
        ]
