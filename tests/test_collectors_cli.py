from __future__ import annotations

import io
import subprocess
import sys
import unittest
from pathlib import Path

from collectors.base import CollectionOptions, CollectionResult
from collectors.cli import main
from collectors.errors import CollectorConfigurationError
from collectors.registry import CollectorRegistry


ROOT = Path(__file__).resolve().parents[1]


class FakeCollector:
    source_id = "fake-source"

    def __init__(self) -> None:
        self.was_called = False

    def collect(
        self,
        options: CollectionOptions | None = None,
    ) -> CollectionResult:
        self.was_called = True
        return CollectionResult(
            source_id=self.source_id,
            request_count=1,
            item_count=2,
            detail_count=0,
            stored_paths=(Path("first.json"), Path("second.json")),
        )


class CollectorCliTests(unittest.TestCase):
    def test_source_selects_and_runs_registered_collector(self) -> None:
        registry = CollectorRegistry()
        collector = FakeCollector()
        registry.register("fake-source", lambda: collector)
        stdout = io.StringIO()
        stderr = io.StringIO()

        result = main(
            ["--source", "fake-source"],
            registry=registry,
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(0, result)
        self.assertTrue(collector.was_called)
        self.assertEqual(
            "collector completed: source=fake-source "
            "requests=1 items=2 details=0 raw_documents=2\n",
            stdout.getvalue(),
        )
        self.assertEqual("", stderr.getvalue())

    def test_unknown_source_returns_safe_failure(self) -> None:
        stderr = io.StringIO()

        result = main(
            ["--source", "unknown-source"],
            registry=CollectorRegistry(),
            stderr=stderr,
        )

        self.assertEqual(1, result)
        self.assertIn("unknown source ID", stderr.getvalue())

    def test_duplicate_source_registration_is_rejected(self) -> None:
        registry = CollectorRegistry()
        registry.register("fake-source", FakeCollector)

        with self.assertRaises(CollectorConfigurationError):
            registry.register("fake-source", FakeCollector)

    def test_factory_source_id_must_match_registry_entry(self) -> None:
        registry = CollectorRegistry()
        registry.register("other-source", FakeCollector)

        with self.assertRaises(CollectorConfigurationError):
            registry.create("other-source")

    def test_unexpected_collector_error_message_is_not_exposed(self) -> None:
        class FailingCollector:
            source_id = "failing-source"

            def collect(
                self,
                options: CollectionOptions | None = None,
            ) -> CollectionResult:
                raise RuntimeError("apiKeyNm=secret-value")

        registry = CollectorRegistry()
        registry.register("failing-source", FailingCollector)
        stderr = io.StringIO()

        result = main(
            ["--source", "failing-source"],
            registry=registry,
            stderr=stderr,
        )

        self.assertEqual(1, result)
        self.assertNotIn("secret-value", stderr.getvalue())
        self.assertEqual(
            "collector failed unexpectedly: source=failing-source\n",
            stderr.getvalue(),
        )

    def test_module_entrypoint_lists_sources(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "collectors", "--list-sources"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            "bokjiro-central-welfare-api\n"
            "cheonan-youthcenter-web\n"
            "kinfa-financial-product-web\n"
            "kosaf-scholarship-web\n"
            "lh-housing-announcement-web\n"
            "regional-busan-youth-platform\n"
            "regional-gyeongbuk-youth-platform\n"
            "work24-policy-web\n"
            "youthcenter-api\n",
            result.stdout,
        )
        self.assertEqual("", result.stderr)


if __name__ == "__main__":
    unittest.main()
