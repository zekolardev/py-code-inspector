
import unittest

from py_code_inspector.inspector import inspect_code


class InspectorTests(unittest.TestCase):
    def test_valid_code_has_no_syntax_error(self):
        issues = inspect_code("x = 1\n")
        self.assertFalse(any(issue.code == "E001" for issue in issues))

    def test_syntax_error_is_reported(self):
        issues = inspect_code("def broken(:\n")
        self.assertTrue(any(issue.code == "E001" for issue in issues))

    def test_function_naming_issue_is_reported(self):
        issues = inspect_code("def BadName():\n    return 1\n")
        self.assertTrue(any(issue.code == "S001" for issue in issues))

    def test_class_naming_issue_is_reported(self):
        issues = inspect_code("class bad_class:\n    pass\n")
        self.assertTrue(any(issue.code == "S001" for issue in issues))

    def test_long_comment_is_reported(self):
        comment = "#" + ("a" * 121)
        issues = inspect_code(comment + "\n")
        self.assertTrue(any(issue.code == "S002" for issue in issues))

    def test_unused_variable_is_reported(self):
        issues = inspect_code(
            "def calculate():\n"
            "    total = 10\n"
            "    return 1\n"
        )
        self.assertTrue(
            any(
                issue.code == "W001" and "total" in issue.message
                for issue in issues
            )
        )

    def test_used_variable_is_not_reported(self):
        issues = inspect_code(
            "def calculate():\n"
            "    total = 10\n"
            "    return total\n"
        )
        self.assertFalse(
            any(
                issue.code == "W001" and "total" in issue.message
                for issue in issues
            )
        )

    def test_function_without_snake_case_is_reported(self):
        issues = inspect_code("def badName():\n    return 1\n")
        self.assertTrue(any(issue.code == "S001" for issue in issues))

    def test_function_with_mixed_case_and_underscore_is_reported(self):
        issues = inspect_code("def bad_Name():\n    return 1\n")
        self.assertTrue(any(issue.code == "S001" for issue in issues))

    def test_valid_snake_case_function_is_accepted(self):
        issues = inspect_code("def calculate_total():\n    return 1\n")
        self.assertFalse(any(issue.code == "S001" for issue in issues))

    def test_variable_used_in_nested_function_is_not_reported(self):
        source = (
            "def outer():\n"
            "    message = 'hello'\n"
            "    def inner():\n"
            "        return message\n"
            "    return inner()\n"
        )
        issues = inspect_code(source)
        self.assertFalse(
            any(
                issue.code == "W001" and "message" in issue.message
                for issue in issues
            )
        )

    def test_reassigned_unused_variable_is_reported_once(self):
        source = (
            "def calculate():\n"
            "    total = 10\n"
            "    total = 20\n"
            "    return 1\n"
        )
        issues = inspect_code(source)
        matching = [
            issue for issue in issues
            if issue.code == "W001" and "total" in issue.message
        ]
        self.assertEqual(len(matching), 1)

    def test_variable_used_in_condition_is_not_reported(self):
        source = (
            "def check():\n"
            "    is_ready = True\n"
            "    if is_ready:\n"
            "        return 1\n"
            "    return 0\n"
        )
        issues = inspect_code(source)
        self.assertFalse(
            any(
                issue.code == "W001" and "is_ready" in issue.message
                for issue in issues
            )
        )

    def test_variable_used_in_loop_is_not_reported(self):
        source = (
            "def calculate():\n"
            "    count = 3\n"
            "    for index in range(count):\n"
            "        print(index)\n"
        )
        issues = inspect_code(source)
        self.assertFalse(
            any(
                issue.code == "W001"
                and any(name in issue.message for name in ("count", "index"))
                for issue in issues
            )
        )

    def test_unused_variable_in_nested_function_is_reported(self):
        source = (
            "def outer():\n"
            "    def inner():\n"
            "        temporary = 10\n"
            "        return 1\n"
            "    return inner()\n"
        )
        issues = inspect_code(source)
        self.assertTrue(
            any(
                issue.code == "W001" and "temporary" in issue.message
                for issue in issues
            )
        )


if __name__ == "__main__":
    unittest.main()

