from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_docs.py"
SPEC = importlib.util.spec_from_file_location("validate_docs", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
validate_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_docs)


class DocumentationValidationTests(unittest.TestCase):
    def test_broken_relative_link_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = root / "docs" / "index.md"
            document.parent.mkdir(parents=True)
            document.write_text("[missing](missing.md)\n", encoding="utf-8")

            errors = validate_docs.check_markdown_links(root, [document])

            self.assertTrue(any("broken link target" in error for error in errors))

    def test_existing_relative_and_external_links_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docs = root / "docs"
            docs.mkdir()
            target = docs / "target.md"
            target.write_text("# target\n", encoding="utf-8")
            document = docs / "index.md"
            document.write_text(
                "[local](target.md) [web](https://example.com)\n",
                encoding="utf-8",
            )

            errors = validate_docs.check_markdown_links(root, [document])

            self.assertEqual([], errors)

    def test_legacy_project_name_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = root / "README.md"
            document.write_text("open-youth-policy\n", encoding="utf-8")

            errors = validate_docs.check_forbidden_names(root, [document])

            self.assertEqual(1, len(errors))

    def test_secret_assignment_and_safe_placeholder_are_distinguished(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unsafe = root / "unsafe.md"
            safe = root / "safe.md"
            unsafe.write_text("API_KEY=real-looking-value\n", encoding="utf-8")
            safe.write_text(
                "API_KEY=your-api-key\n"
                "ADMIN_PIN_HASH=<sha256-of-four-digit-pin>\n",
                encoding="utf-8",
            )

            errors = validate_docs.check_secret_assignments(root, [unsafe, safe])

            self.assertEqual(1, len(errors))
            self.assertIn("unsafe.md", errors[0])

    def test_admin_secret_assignment_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = root / "security.md"
            document.write_text(
                "ADMIN_TOKEN_SECRET=not-a-placeholder\n",
                encoding="utf-8",
            )

            errors = validate_docs.check_secret_assignments(root, [document])

            self.assertEqual(1, len(errors))

    def test_empty_document_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docs = root / "docs"
            docs.mkdir()
            (docs / "empty.md").touch()

            errors = validate_docs.check_empty_docs(root)

            self.assertEqual(1, len(errors))


if __name__ == "__main__":
    unittest.main()
