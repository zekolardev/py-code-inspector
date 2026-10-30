import unittest
from py_code_inspector.inspector import inspect_code


class ScopeAndExceptionTests(unittest.TestCase):
    def test_bare_except_is_reported(self):
        issues = inspect_code("try:\n    risky()\nexcept:\n    pass\n")
        self.assertIn("S004", [issue.code for issue in issues])

    def test_typed_except_is_not_reported(self):
        issues = inspect_code("try:\n    risky()\nexcept ValueError:\n    pass\n")
        self.assertNotIn("S004", [issue.code for issue in issues])

    def test_syntax_error_is_reported(self):
        issues = inspect_code("def broken(:\n    pass\n")
        self.assertEqual(issues[0].code, "E001")

    def test_module_variable_used_in_function_is_not_unused(self):
        issues = inspect_code("VALUE = 10\ndef get_value():\n    return VALUE\n")
        self.assertFalse(
            any(
                issue.code == "W002"
                and "VALUE" in issue.message
                for issue in issues
            )
        )


if __name__ == "__main__":
    unittest.main()

