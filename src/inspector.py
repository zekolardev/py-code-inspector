
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

        arguments = (
            node.args.posonlyargs
            + node.args.args
            + node.args.kwonlyargs
        )

        local_names = {argument.arg for argument in arguments}

        if node.args.vararg:
            local_names.add(node.args.vararg.arg)

        if node.args.kwarg:
            local_names.add(node.args.kwarg.arg)

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
                    if isinstance(
                        child,
                        (ast.FunctionDef, ast.AsyncFunctionDef),
                    ):
                        nested_functions.append(child)
                    continue

                if isinstance(child, ast.Name):
                    if isinstance(child.ctx, ast.Store):
                        assigned.setdefault(child.id, child.lineno)
                        local_names.add(child.id)
                    elif isinstance(child.ctx, ast.Load):
                        used.add(child.id)

                collect(child)

        for statement in node.body:
            if isinstance(
                statement,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                nested_functions.append(statement)
                continue

            collect(statement)

        for nested in nested_functions:
            used.update(self._get_free_names(nested))

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
                    )
                )

        for nested in nested_functions:
            self._analyze_function(nested)

    @staticmethod
    def _get_free_names(function_node):
        """Return names loaded by a nested function but not defined locally."""
        assigned = set()
        loaded = set()

        arguments = (
            function_node.args.posonlyargs
            + function_node.args.args
            + function_node.args.kwonlyargs
        )
        assigned.update(argument.arg for argument in arguments)

        if function_node.args.vararg:
            assigned.add(function_node.args.vararg.arg)

        if function_node.args.kwarg:
            assigned.add(function_node.args.kwarg.arg)

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
                    continue

                if isinstance(child, ast.Name):
                    if isinstance(child.ctx, ast.Store):
                        assigned.add(child.id)
                    elif isinstance(child.ctx, ast.Load):
                        loaded.add(child.id)

                collect(child)

        for statement in function_node.body:
            if isinstance(
                statement,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                continue

            collect(statement)

        return loaded - assigned


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


def _check_unused_variables(tree):
    analyzer = FunctionAnalyzer()
    analyzer.visit(tree)
    return analyzer.issues


def _get_assigned_names(target):
    """Extract names assigned by an assignment target."""
    if isinstance(target, ast.Name):
        return [(target.id, target.lineno)]

    if isinstance(target, (ast.Tuple, ast.List)):
        names = []
        for element in target.elts:
            names.extend(_get_assigned_names(element))
        return names

    return []


def _check_module_variables(tree):
    """Check module-level assignments for naming and unused variables."""
    issues = []
    assigned = {}

    for statement in tree.body:
        targets = []

        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                targets.extend(_get_assigned_names(target))
        elif isinstance(statement, ast.AnnAssign):
            targets.extend(_get_assigned_names(statement.target))
        elif isinstance(statement, ast.AugAssign):
            targets.extend(_get_assigned_names(statement.target))

        for name, line in targets:
            if name.startswith("__") and name.endswith("__"):
                continue

            assigned.setdefault(name, line)

            if not re.fullmatch(r"[A-Z][A-Z0-9_]*", name):
                issues.append(
                    Issue(
                        code="S003",
                        message=(
                            f"Use UPPER_SNAKE_CASE for module-level "
                            f"constant '{name}'."
                        ),
                        line=line,
                    )
                )

    # Collect names referenced anywhere in the module, including functions.
    loaded_names = set()

    class LoadNameVisitor(ast.NodeVisitor):
        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load):
                loaded_names.add(node.id)

    LoadNameVisitor().visit(tree)

    for name, line in assigned.items():
        if name not in loaded_names and not name.startswith("_"):
            issues.append(
                Issue(
                    code="W002",
                    message=f"Unused module-level variable '{name}'.",
                    line=line,
                )
            )

    return issues


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
    issues.extend(_check_module_variables(tree))
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
