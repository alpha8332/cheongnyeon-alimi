from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SecretBoundaryTests(unittest.TestCase):
    def check_ignored(self, path: str) -> bool:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "--quiet", "--", path],
            cwd=ROOT,
            check=False,
        )
        return result.returncode == 0

    def test_secret_and_runtime_paths_are_ignored(self) -> None:
        ignored_paths = (
            "APIkey.txt",
            ".env",
            ".env.local",
            "opensource_plan/api_info/공공 API 사용법 (온통청년, 복지로).docx",
            "runtime/raw/youthcenter-api/response.json",
            "data/runtime/raw/bokjiro-central-welfare-api/response.xml",
        )

        for path in ignored_paths:
            with self.subTest(path=path):
                self.assertTrue(self.check_ignored(path))

    def test_safe_environment_example_is_not_ignored(self) -> None:
        self.assertFalse(self.check_ignored(".env.example"))


if __name__ == "__main__":
    unittest.main()
