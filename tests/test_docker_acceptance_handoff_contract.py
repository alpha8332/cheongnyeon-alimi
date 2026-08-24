from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_transfer_package_uses_interactive_encrypted_7zip_outside_workspace():
    script = (
        ROOT
        / "deployment"
        / "postgres"
        / "create_acceptance_transfer_package.ps1"
    ).read_text(encoding="utf-8")

    assert "DEP5_BLOCKED: transfer package output must stay outside the workspace" in script
    assert '"-mhe=on"' in script
    assert '"-p"' in script
    assert '@("t", "--", $PartialArchivePath)' in script
    assert '@("t", "-p", "--", $PartialArchivePath)' not in script
    assert "DEP5_PASSPHRASE_PROMPT" in script
    assert "DEP5_PASSPHRASE_VERIFY" in script
    assert "7zip-portable\\7zr.exe" in script
    assert "Read-Host" not in script
    assert "SecureStringToBSTR" not in script
    assert "passphrase =" not in script.lower()
    assert "refusing to overwrite" in script
    assert "status = \"DEP5_TRANSFER_PACKAGE_VERIFIED\"" in script


def test_handoff_requires_matching_identity_and_independent_role_receipts():
    handoff = (
        ROOT
        / "docs"
        / "development"
        / "handoff"
        / "docker_acceptance"
        / "README.md"
    ).read_text(encoding="utf-8")

    for required in (
        "acceptance-20260819-75510a9",
        "46810a6ac6082680d2fae17ab98721597ec4b5e23ec667b3d086b5a4e9739a8b",
        "Backend 담당자",
        "Frontend 담당자",
        "사용성 리뷰어",
        "QA 담당자",
        "DOCKER_ACCEPTANCE_BLOCKED",
        "DOCKER_ACCEPTANCE_PASS",
        "7z.exe x -o'C:\\received\\acceptance-snapshot'",
    ):
        assert required in handoff


def test_result_and_defect_templates_separate_skip_and_independent_retest():
    result_template = (
        ROOT
        / "docs"
        / "development"
        / "handoff"
        / "docker_acceptance"
        / "acceptance_result_template.md"
    ).read_text(encoding="utf-8")
    defect_template = (
        ROOT
        / "docs"
        / "development"
        / "handoff"
        / "docker_acceptance"
        / "defect_report_template.md"
    ).read_text(encoding="utf-8")

    assert "pass / fail / skip" in result_template
    assert "Mock과 actual" in result_template
    assert "secret·Raw payload" in result_template
    assert "독립 재검증" in defect_template
    assert "자기 수정만으로" in defect_template
