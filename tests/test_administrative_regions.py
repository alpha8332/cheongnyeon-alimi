from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from collectors.regions import (
    RegionReference,
    RegionResolutionStatus,
    RegionStatus,
)


ROOT = Path(__file__).resolve().parents[1]
REGION_SEED = ROOT / "data" / "seeds" / "administrative_regions.json"
ALIAS_SEED = (
    ROOT / "data" / "seeds" / "administrative_region_aliases.json"
)
MANIFEST = (
    ROOT
    / "data"
    / "reference"
    / "administrative_regions"
    / "legal_dong_codes_20260803.manifest.json"
)


class AdministrativeRegionSeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reference = RegionReference.from_seed_files(
            REGION_SEED, ALIAS_SEED
        )

    def test_locked_official_snapshot_counts_and_checksum(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("kr-bjd-20260803", manifest["scheme"])
        self.assertEqual(53387, manifest["record_count"])
        self.assertEqual(20560, manifest["active_count"])
        self.assertEqual(32827, manifest["retired_count"])
        self.assertEqual(
            "dd2235aee1748602616da06212a0f973a18212d2e044318fdc55fe5e33d08feb",
            manifest["normalized_csv_sha256"],
        )

    def test_seed_is_reproducible(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "scripts/build_administrative_regions.py",
                "--snapshot-date",
                "2026-08-03",
                "--check",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_policy_region_subset_counts_and_integrity(self) -> None:
        self.assertEqual(538, len(self.reference.regions))
        self.assertEqual(
            285,
            sum(
                region.status is RegionStatus.ACTIVE
                for region in self.reference.regions
            ),
        )
        self.assertEqual(
            253,
            sum(
                region.status is RegionStatus.RETIRED
                for region in self.reference.regions
            ),
        )
        self.assertEqual(1080, len(self.reference.aliases))

    def test_cheonan_and_district_ancestor_paths(self) -> None:
        self.assertEqual(
            ["4400000000", "0000000000"],
            [
                region.code
                for region in self.reference.ancestors("4413000000")
            ],
        )
        self.assertEqual(
            ["4413000000", "4400000000", "0000000000"],
            [
                region.code
                for region in self.reference.ancestors("4413100000")
            ],
        )
        district = self.reference.get("4413100000")
        assert district is not None
        self.assertEqual("4400000000", district.source_parent_code)
        self.assertEqual("4413000000", district.aggregate_parent_code)

    def test_alias_resolution_preserves_homonym_ambiguity(self) -> None:
        self.assertEqual(
            "4413000000",
            self.reference.resolve_alias("천안").candidates[0].code,
        )
        self.assertEqual(
            "4400000000",
            self.reference.resolve_alias("충남").candidates[0].code,
        )
        self.assertEqual(
            "0000000000",
            self.reference.resolve_alias("전국").candidates[0].code,
        )
        homonym = self.reference.resolve_alias("중구")
        self.assertEqual(RegionResolutionStatus.AMBIGUOUS, homonym.status)
        self.assertGreater(len(homonym.candidates), 1)

    def test_external_code_resolution_is_exact_and_unknown_is_visible(self) -> None:
        matched = self.reference.resolve_external_code(
            "kr-bjd-prefix5", "44131"
        )
        self.assertEqual(RegionResolutionStatus.MATCHED, matched.status)
        self.assertEqual("4413100000", matched.candidates[0].code)

        for value in ("4413", "99999"):
            with self.subTest(value=value):
                result = self.reference.resolve_external_code(
                    "kr-bjd-prefix5", value
                )
                self.assertEqual(
                    RegionResolutionStatus.UNMAPPED, result.status
                )
                self.assertEqual((), result.candidates)

    def test_retired_code_is_retained_without_successor_inference(self) -> None:
        retired = self.reference.get("4405000000")
        assert retired is not None
        self.assertEqual(RegionStatus.RETIRED, retired.status)
        self.assertIsNone(retired.aggregate_parent_code)
        self.assertEqual(
            RegionResolutionStatus.UNMAPPED,
            self.reference.resolve_external_code(
                "kr-bjd-prefix5", "44050"
            ).status,
        )
        historical = self.reference.resolve_external_code(
            "kr-bjd-prefix5", "44050", active_only=False
        )
        self.assertEqual(RegionResolutionStatus.MATCHED, historical.status)
        self.assertEqual("4405000000", historical.candidates[0].code)


if __name__ == "__main__":
    unittest.main()
