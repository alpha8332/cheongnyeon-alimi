import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import select

from app.models.administrative_region import AdministrativeRegion
from app.services.region_reference_importer import (
    RegionReferenceImportError,
    import_region_reference,
)


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
REGIONS_PATH = ROOT / "data" / "seeds" / "administrative_regions.json"
ALIASES_PATH = (
    ROOT / "data" / "seeds" / "administrative_region_aliases.json"
)


def test_region_reference_import_is_complete_and_idempotent(db):
    first = import_region_reference(db, REGIONS_PATH, ALIASES_PATH)
    second = import_region_reference(db, REGIONS_PATH, ALIASES_PATH)

    assert first.inserted_regions == 538
    assert first.inserted_aliases == 1080
    assert first.committed is True
    assert second.unchanged_regions == 538
    assert second.unchanged_aliases == 1080
    assert second.inserted_regions == 0
    assert second.inserted_aliases == 0

    dongnam = db.get(
        AdministrativeRegion,
        ("kr-bjd-20260803", "4413100000"),
    )
    assert dongnam is not None
    assert dongnam.parent_code == "4400000000"
    assert dongnam.aggregate_parent_code == "4413000000"


def test_region_reference_dry_run_rolls_back(db):
    result = import_region_reference(
        db,
        REGIONS_PATH,
        ALIASES_PATH,
        dry_run=True,
    )

    assert result.inserted_regions == 538
    assert result.inserted_aliases == 1080
    assert result.committed is False
    assert db.scalar(select(AdministrativeRegion).limit(1)) is None


def test_region_reference_rejects_drift_in_versioned_scheme(db):
    import_region_reference(db, REGIONS_PATH, ALIASES_PATH)
    cheonan = db.get(
        AdministrativeRegion,
        ("kr-bjd-20260803", "4413000000"),
    )
    assert cheonan is not None
    cheonan.name = "변조된 이름"
    db.commit()

    with pytest.raises(RegionReferenceImportError):
        import_region_reference(db, REGIONS_PATH, ALIASES_PATH)


def test_region_reference_cli_module_loads_from_backend_directory():
    completed = subprocess.run(
        [sys.executable, "-B", "-m", "app.cli.import_regions", "--help"],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "Import locked administrative-region Seed" in completed.stdout
