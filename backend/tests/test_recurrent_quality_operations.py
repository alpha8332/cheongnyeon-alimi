import copy
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.policy import Policy
from app.services import seed_importer
from app.services.seed_importer import import_programs


ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = ROOT / "data" / "seeds" / "initial_programs.json"
CONTRACT_PATH = (
    ROOT
    / "data"
    / "fixtures"
    / "contracts"
    / "recurrent_quality_cases.json"
)


def _contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _case(case_id):
    return next(
        case for case in _contract()["cases"] if case["id"] == case_id
    )


def _programs():
    contract = _contract()
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    return [copy.deepcopy(seed[index]) for index in contract["base_seed_indexes"]]


@pytest.mark.parametrize(
    "case_id",
    ("same_snapshot", "collection_metadata_only", "single_business_field"),
)
def test_recurrent_change_classification_contract(db, case_id):
    case = _case(case_id)
    programs = _programs()
    first = import_programs(db, programs)
    assert first.inserted == 2
    db.commit()

    rerun = copy.deepcopy(programs)
    patch_values = case.get("patch", {})
    if "collected_at" in patch_values:
        target = rerun[case["target_index"]]
        target["collected_at"] = patch_values["collected_at"]
        for evidence in target["provenance"]:
            evidence["collected_at"] = patch_values[
                "provenance_collected_at"
            ]
    if "title" in patch_values:
        rerun[case["target_index"]]["title"] = patch_values["title"]

    result = import_programs(db, rerun)

    assert result.updated == case["expected"]["updated"]
    assert result.unchanged == case["expected"]["unchanged"]
    assert result.duplicate == case["expected"]["duplicate"]


def test_duplicate_identity_is_counted_and_first_candidate_is_canonical(db):
    case = _case("duplicate_in_run")
    programs = _programs()
    duplicate = copy.deepcopy(programs[case["target_index"]])
    programs.append(duplicate)

    result = import_programs(db, programs)

    expected = case["expected"]
    assert result.accepted == expected["accepted"]
    assert result.inserted == expected["inserted"]
    assert result.duplicate == expected["duplicate"]
    assert db.query(Policy).count() == expected["stored"]
    issue = next(issue for issue in result.issues if issue.code == expected["issue_code"])
    assert issue.stage == expected["issue_stage"]


def test_invalid_fixture_is_validate_stage_and_preserves_atomic_batch(db):
    case = _case("invalid_batch")
    programs = _programs()
    programs[case["target_index"]].pop(case["field"])

    result = import_programs(db, programs)

    expected = case["expected"]
    assert result.inserted == expected["inserted"]
    assert result.rejected == expected["rejected"]
    assert result.committed is expected["committed"]
    assert all(issue.stage == expected["issue_stage"] for issue in result.issues)
    assert db.query(Policy).count() == 0


def test_persist_failure_is_safe_and_rolls_back_the_accepted_batch(db):
    case = _case("persist_failure")
    programs = _programs()
    portable_upsert = seed_importer._portable_upsert
    calls = 0

    def fail_second_write(session, values):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise SQLAlchemyError("credential=do-not-expose")
        return portable_upsert(session, values)

    with patch(
        "app.services.seed_importer._portable_upsert",
        side_effect=fail_second_write,
    ):
        result = import_programs(db, programs)

    expected = case["expected"]
    assert result.inserted == expected["inserted"]
    assert result.failed == expected["failed"]
    assert result.committed is expected["committed"]
    assert result.issues[0].code == expected["issue_code"]
    assert result.issues[0].stage == expected["issue_stage"]
    assert "do-not-expose" not in repr(result)
    assert db.query(Policy).count() == 0
