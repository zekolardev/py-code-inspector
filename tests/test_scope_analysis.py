
import unittest

from src.inspector import inspect_code


class ScopeAnalysisTests(unittest.TestCase):
    def test_global_variable_is_not_reported_as_local_unused(self):
        source = """
VALUE = 10

def update_value():
    global VALUE
    VALUE = 20
"""
        issues = inspect_code(source)
        self.assertFalse(
            any(
                issue.code == "W001"
                and "VALUE" in issue.message
                for issue in issues
            )
        )

    def test_nonlocal_variable_used_by_nested_function(self):
        source = """
def outer():
    value = 10

    def inner():
        nonlocal value
        value = 20

    inner()
"""
        issues = inspect_code(source)
        self.assertFalse(
            any(
                issue.code == "W001"
                and "value" in issue.message
                for issue in issues
            )
        )

    def test_local_variable_does_not_count_as_module_variable_usage(self):
        source = """
value = 10

def calculate():
    value = 20
    return value
"""
        issues = inspect_code(source)
        self.assertTrue(
            any(
                issue.code == "W002"
                and "'value'" in issue.message
                for issue in issues
            )
        )

    def test_nested_function_can_read_outer_variable(self):
        source = """
def outer():
    message = "hello"

    def inner():
        return message

    return inner
"""
        issues = inspect_code(source)
        self.assertFalse(
            any(
                issue.code == "W001"
                and "'message'" in issue.message
                for issue in issues
            )
        )

    def test_unused_local_variable_is_still_reported(self):
        source = """
def calculate():
    unused_value = 42
"""
        issues = inspect_code(source)
        self.assertTrue(
            any(
                issue.code == "W001"
                and "'unused_value'" in issue.message
                for issue in issues
            )
        )


if __name__ == "__main__":
    unittest.main()
