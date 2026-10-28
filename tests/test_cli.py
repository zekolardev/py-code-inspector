
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CLITests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "src.cli", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_json_output_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            sample = Path(directory) / "sample.py"
            sample.write_text("print('hello')\n", encoding="utf-8")

            result = self.run_cli(str(sample), "--format", "json")

            self.assertEqual(result.returncode, 0)
            data = json.loads(result.stdout)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["file"], str(sample))
            self.assertEqual(data[0]["issues"], [])

    def test_missing_path_returns_error(self):
        result = self.run_cli("this_path_should_not_exist_12345")

        self.assertEqual(result.returncode, 2)
        self.assertIn("Error: path does not exist", result.stderr)

    def test_issues_return_exit_code_one(self):
        with tempfile.TemporaryDirectory() as directory:
            sample = Path(directory) / "sample.py"
            sample.write_text(
                "def CalculateTotal():\n"
                "    unused_value = 100\n"
                "    return 50\n",
                encoding="utf-8",
            )

            result = self.run_cli(str(sample))

            self.assertEqual(result.returncode, 1)
            self.assertIn("[S001]", result.stdout)
            self.assertIn("[W001]", result.stdout)

    def test_json_report_is_saved_to_file(self):
        with tempfile.TemporaryDirectory() as directory:
            sample = Path(directory) / "sample.py"
            report = Path(directory) / "report.json"
            sample.write_text("print('hello')\n", encoding="utf-8")

            result = self.run_cli(
                str(sample),
                "--format",
                "json",
                "--output",
                str(report),
            )

            self.assertEqual(result.returncode, 0)
            self.assertTrue(report.exists())

            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data[0]["issues"], [])
            self.assertIn("Report saved to", result.stdout)


if __name__ == "__main__":
    unittest.main()
