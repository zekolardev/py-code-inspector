import ast
import re
from dataclasses import dataclass


@dataclass
class Issue:
    code: str
    message: str
    line: int
    severity: str = "warning"


class _FunctionScope:
    """Collect assignments and reads within one function scope."""

    def __init__(self, node):
        self.node = node
        self.assigned = {}
        self.loaded = set()
        self.globals = set()
        self.nonlocals = set()
        self.children = []
        self._collect()

    def _collect(self):
        args = (
            self.node.args.posonlyargs
            + self.node.args.args
            + self.node.args.kwonlyargs
        )

        if self.node.args.vararg:
            args.append(self.node.args.vararg)

        if self.node.args.kwarg:
            args.append(self.node.args.kwarg)

        for arg in args:
            self.assigned.setdefault(arg.arg, arg.lineno)

        scope = self

        class Collector(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                if node is scope.node:
                    for statement in node.body:
                        self.visit(statement)
                else:
                    scope.children.append(node)

            def visit_AsyncFunctionDef(self, node):
                if node is scope.node:
                    for statement in node.body:
                        self.visit(statement)
                else:
                    scope.children.append(node)

            def visit_Lambda(self, node):
                return

            def visit_ClassDef(self, node):
                return

            def visit_Global(self, node):
                scope.globals.update(node.names)

            def visit_Nonlocal(self, node):
                scope.nonlocals.update(node.names)

            def visit_Name(self, node):
                if isinstance(node.ctx, (ast.Store, ast.Param)):
                    scope.assigned.setdefault(node.id, node.lineno)
                elif isinstance(node.ctx, ast.Load):
                    scope.loaded.add(node.id)

        collector = Collector()

        for statement in self.node.body:
            collector.visit(statement)

        for name in self.globals | self.nonlocals:
            self.assigned.pop(name, None)

    def unused_assignments(self):
        ignored = self.globals | self.nonlocals

        return [
            (name, line)
            for name, line in self.assigned.items()
            if name not in self.loaded
            and name not in ignored
            and not name.startswith("_")
        ]


class FunctionAnalyzer(ast.NodeVisitor):
    """Detect unused local variables."""

    def __init__(self):
        self.issues = []

    def visit_FunctionDef(self, node):
        self._analyze(node)

    def visit_AsyncFunctionDef(self, node):
        self._analyze(node)

    def _analyze(self, node):
        scope = _FunctionScope(node)

        for child in scope.children:
            child_scope = _FunctionScope(child)

            referenced_names = (
                child_scope.loaded | child_scope.nonlocals
            )

            for name in referenced_names:
                if name in scope.assigned:
                    scope.loaded.add(name)

        for name, line in scope.unused_assignments():
            self.issues.append(
                Issue(
                    code="W001",
                    message=f"Unused variable '{name}'.",
                    line=line,
                )
            )

        for child in scope.children:
            self._analyze(child)


def _check_names(tree):
    issues = []
    pattern = re.compile(r"^[a-z_][a-z0-9_]*$")

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
            valid = bool(pattern.fullmatch(name))
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
    if isinstance(target, ast.Name):
        return [(target.id, target.lineno)]

    if isinstance(target, (ast.Tuple, ast.List)):
        result = []

        for item in target.elts:
            result.extend(_get_assigned_names(item))

        return result

    return []


def _module_loads(tree):
    """Find module-level names referenced in functions and classes."""
    loaded = set()

    class ModuleVisitor(ast.NodeVisitor):
        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load):
                loaded.add(node.id)

        def visit_FunctionDef(self, node):
            local = _FunctionScope(node)
            loaded.update(local.loaded - set(local.assigned))
            loaded.update(local.globals)

            for child in local.children:
                self.visit(child)

        def visit_AsyncFunctionDef(self, node):
            self.visit_FunctionDef(node)

        def visit_ClassDef(self, node):
            for statement in node.body:
                self.visit(statement)

    visitor = ModuleVisitor()

    for statement in tree.body:
        visitor.visit(statement)

    return loaded


def _check_module_variables(tree):
    issues = []
    assigned = {}

    for statement in tree.body:
        targets = []

        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                targets.extend(_get_assigned_names(target))

        elif isinstance(statement, (ast.AnnAssign, ast.AugAssign)):
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
                            "Use UPPER_SNAKE_CASE for module-level "
                            f"constant '{name}'."
                        ),
                        line=line,
                    )
                )

    loaded = _module_loads(tree)

    for name, line in assigned.items():
        if name not in loaded and not name.startswith("_"):
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


def _check_bare_except(tree):
    issues = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            issues.append(
                Issue(
                    code="S004",
                    message=(
                        "Avoid bare 'except:'. "
                        "Catch a specific exception type instead."
                    ),
                    line=node.lineno,
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
    issues.extend(_check_bare_except(tree))

    return sorted(
        issues,
        key=lambda issue: (issue.line, issue.code),
    )


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
