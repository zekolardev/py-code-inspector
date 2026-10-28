
import tempfile
import unittest
from pathlib import Path

from src.inspector import inspect_code, inspect_file


class InspectCodeTests(unittest.TestCase):
    def test_valid_code_has_no_issues(self):
        source = "def add_numbers(a, b):\n    return a + b\n"
        self.assertEqual(inspect_code(source), [])

    def test_syntax_error_is_reported(self):
        issues = inspect_code("def broken(:\n    pass\n")
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, "E001")
        self.assertEqual(issues[0].severity, "error")

    def test_unused_variable_is_reported(self):
        issues = inspect_code("def calculate():\n    result = 10\n")
        self.assertTrue(any(issue.code == "W001" for issue in issues))

    def test_function_naming_style_is_reported(self):
        issues = inspect_code("def CalculateTotal():\n    return 1\n")
        self.assertTrue(any(issue.code == "S001" for issue in issues))

    def test_long_comment_is_reported(self):
        source = "# " + ("a" * 90) + "\nvalue = 1\nprint(value)\n"
        issues = inspect_code(source)
        self.assertTrue(any(issue.code == "S002" for issue in issues))

    def test_inspect_file_reads_python_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text(
                "value = 1\nprint(value)\n",
                encoding="utf-8",
            )
            self.assertEqual(inspect_file(path), [])

    def test_missing_file_returns_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.py"
            issues = inspect_file(path)
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0].code, "E002")

    def test_unused_variable_in_nested_function_is_reported(self):
        source = (
            "def outer():\n"
            "    def inner():\n"
            "        unused_value = 10\n"
            "        return 1\n"
            "    return inner()\n"
        )
        issues = inspect_code(source)
        self.assertTrue(
            any(
                issue.code == "W001"
                and "'unused_value'" in issue.message
                for issue in issues
            )
        )

    def test_nested_function_name_is_not_reported_as_unused(self):
        source = (
            "def outer():\n"
            "    def inner():\n"
            "        return 1\n"
            "    return inner()\n"
        )
        issues = inspect_code(source)
        self.assertFalse(
            any(
                issue.code == "W001"
                and "'inner'" in issue.message
                for issue in issues
            )
        )

    def test_unused_function_parameter_is_not_reported(self):
        source = "def greet(name):\n    return 'hello'\n"
        issues = inspect_code(source)
        self.assertFalse(any(issue.code == "W001" for issue in issues))


if __name__ == "__main__":
    unittest.main()
