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
    def test_missing_relative_link_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            document = root / "docs" / "index.md"
            document.parent.mkdir(parents=True)
            document.write_text("[missing](missing.md)\n", encoding="utf-8")

            errors = validate_docs.check_markdown_links(root, [document])

            self.assertEqual(1, len(errors))
            self.assertIn("broken link target", errors[0])

    def test_legacy_project_name_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            document = root / "README.md"
            document.write_text("open-youth-policy\n", encoding="utf-8")

            errors = validate_docs.check_forbidden_names(root, [document])

            self.assertEqual(1, len(errors))
            self.assertIn("legacy project name", errors[0])

    def test_secret_assignment_is_reported_but_placeholder_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            unsafe = root / "unsafe.md"
            safe = root / "safe.md"
            unsafe.write_text("API_KEY=actual-secret-value\n", encoding="utf-8")
            safe.write_text("API_KEY=your-api-key\n", encoding="utf-8")

            errors = validate_docs.check_secret_assignments(root, [unsafe, safe])

            self.assertEqual(1, len(errors))
            self.assertIn("possible secret value", errors[0])

    def test_bokjiro_secret_assignment_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            document = root / "unsafe.md"
            document.write_text(
                "BOKJIRO_API_KEY=actual-secret-value\n",
                encoding="utf-8",
            )

            errors = validate_docs.check_secret_assignments(root, [document])

            self.assertEqual(1, len(errors))
            self.assertIn("BOKJIRO_API_KEY", errors[0])

    def test_forest_plan_and_note_are_paired(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan_dir = root / "docs/development/develop_plan/integration"
            note_dir = root / "docs/development/development_notes/integration"
            plan_dir.mkdir(parents=True)
            note_dir.mkdir(parents=True)
            plan = "\n".join(
                [
                    "# Test Forest",
                    "",
                    "## 계획 정보",
                    "- 상태: completed",
                    *(f"\n## {heading}" for heading in validate_docs.PLAN_HEADINGS[1:]),
                ]
            )
            note = "\n".join(
                [
                    "# Test Forest",
                    "",
                    "## 작업 정보",
                    "- 상태: completed",
                    *(f"\n## {heading}" for heading in validate_docs.NOTE_HEADINGS[1:]),
                ]
            )
            (plan_dir / "01_test.md").write_text(plan, encoding="utf-8")
            (note_dir / "test.md").write_text(note, encoding="utf-8")

            errors = validate_docs.check_forest_documents(root)

            self.assertEqual([], errors)

    def test_draft_plan_in_owner_area_does_not_require_note(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan_dir = root / "docs/development/develop_plan/data"
            plan_dir.mkdir(parents=True)
            plan = "\n".join(
                [
                    "# Data Pipeline Forest",
                    "",
                    "## 계획 정보",
                    "- 상태: draft",
                    *(f"\n## {heading}" for heading in validate_docs.PLAN_HEADINGS[1:]),
                ]
            )
            (plan_dir / "01_data_pipeline.md").write_text(plan, encoding="utf-8")

            errors = validate_docs.check_forest_documents(root)

            self.assertEqual([], errors)

    def test_in_progress_plan_requires_note_in_same_owner_area(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan_dir = root / "docs/development/develop_plan/data"
            note_dir = root / "docs/development/development_notes/backend"
            plan_dir.mkdir(parents=True)
            note_dir.mkdir(parents=True)
            plan = "\n".join(
                [
                    "# Data Pipeline Forest",
                    "",
                    "## 계획 정보",
                    "- 상태: in-progress",
                    *(f"\n## {heading}" for heading in validate_docs.PLAN_HEADINGS[1:]),
                ]
            )
            note = "\n".join(
                [
                    "# Data Pipeline Forest",
                    "",
                    "## 작업 정보",
                    "- 상태: in-progress",
                    *(f"\n## {heading}" for heading in validate_docs.NOTE_HEADINGS[1:]),
                ]
            )
            (plan_dir / "01_data_pipeline.md").write_text(plan, encoding="utf-8")
            (note_dir / "data_pipeline.md").write_text(note, encoding="utf-8")

            errors = validate_docs.check_forest_documents(root)

            self.assertTrue(
                any("matching development note is missing" in error for error in errors)
            )
            self.assertTrue(
                any("matching numbered develop plan is missing" in error for error in errors)
            )

    def test_unknown_or_nested_owner_area_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan_dir = root / "docs/development/develop_plan/mobile/nested"
            plan_dir.mkdir(parents=True)
            plan = "\n".join(
                [
                    "# Mobile Forest",
                    "",
                    "## 계획 정보",
                    "- 상태: draft",
                    *(f"\n## {heading}" for heading in validate_docs.PLAN_HEADINGS[1:]),
                ]
            )
            (plan_dir / "01_mobile.md").write_text(plan, encoding="utf-8")

            errors = validate_docs.check_forest_documents(root)

            self.assertTrue(
                any("invalid Forest owner area" in error for error in errors)
            )

    def test_forest_documents_must_be_registered_in_readmes_and_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan_dir = root / "docs/development/develop_plan"
            note_dir = root / "docs/development/development_notes"
            plan = plan_dir / "backend/01_favorites.md"
            note = note_dir / "backend/favorites.md"
            index = root / "docs/index.md"
            plan.parent.mkdir(parents=True)
            note.parent.mkdir(parents=True)
            plan.write_text("# Favorites plan\n", encoding="utf-8")
            note.write_text("# Favorites note\n", encoding="utf-8")
            (plan_dir / "README.md").write_text("# Plans\n", encoding="utf-8")
            (note_dir / "README.md").write_text("# Notes\n", encoding="utf-8")
            index.write_text("# Index\n", encoding="utf-8")

            errors = validate_docs.check_forest_indexes(root)

            self.assertEqual(4, len(errors))
            self.assertTrue(any("develop plan README" in error for error in errors))
            self.assertTrue(any("development notes README" in error for error in errors))
            self.assertEqual(2, sum("docs index" in error for error in errors))

    def test_registered_forest_documents_pass_index_check(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan_dir = root / "docs/development/develop_plan"
            note_dir = root / "docs/development/development_notes"
            plan = plan_dir / "frontend/01_calendar.md"
            note = note_dir / "frontend/calendar.md"
            index = root / "docs/index.md"
            plan.parent.mkdir(parents=True)
            note.parent.mkdir(parents=True)
            plan.write_text("# Calendar plan\n", encoding="utf-8")
            note.write_text("# Calendar note\n", encoding="utf-8")
            (plan_dir / "README.md").write_text(
                "[Calendar](frontend/01_calendar.md)\n", encoding="utf-8"
            )
            (note_dir / "README.md").write_text(
                "[Calendar](frontend/calendar.md)\n", encoding="utf-8"
            )
            index.write_text(
                "\n".join(
                    [
                        "[Calendar plan](development/develop_plan/frontend/01_calendar.md)",
                        "[Calendar note](development/development_notes/frontend/calendar.md)",
                    ]
                ),
                encoding="utf-8",
            )

            errors = validate_docs.check_forest_indexes(root)

            self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
