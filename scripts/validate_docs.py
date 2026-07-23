"""Validate the cheongnyeon-alimi documentation system.

The validator intentionally scans project documentation only. Reference planning
artifacts under ``opensource_plan/`` are read-only inputs and are not part of
the published Markdown contract.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote


REQUIRED_FILES = (
    "README.md",
    "CHANGELOG.md",
    "docs/index.md",
    "docs/architecture/README.md",
    "docs/api/README.md",
    "docs/data/README.md",
    "docs/development/README.md",
    "docs/development/develop_plan/README.md",
    "docs/development/development_notes/README.md",
    "docs/governance/README.md",
    "docs/governance/documentation_policy.md",
    "docs/operations/README.md",
    "docs/troubleshooting/README.md",
    "docs/contest/README.md",
)

PLAN_HEADINGS = (
    "계획 정보",
    "목적",
    "범위",
    "범위 밖",
    "선행 조건",
    "공통 설계 원칙",
    "Slice 계획",
    "검증 계획",
    "Forest 완료 기준",
    "위험과 미확정 사항",
    "관련 문서",
)

NOTE_HEADINGS = (
    "작업 정보",
    "목적",
    "Forest 범위",
    "Slice 진행 현황",
    "구현 내용",
    "주요 변경 파일",
    "설계 결정",
    "검증 결과",
    "남은 작업",
)

ALLOWED_STATUSES = {
    "draft",
    "approved",
    "in-progress",
    "completed",
    "superseded",
}

MARKDOWN_LINK = re.compile(r"!?\[[^\]]*]\(([^)]+)\)")
SECRET_ASSIGNMENT = re.compile(
    r"(?im)\b("
    r"YOUTHCENTER_API_KEY|API_KEY|SECRET_KEY|ACCESS_TOKEN|"
    r"PRIVATE_KEY|PASSWORD"
    r")\s*[:=]\s*[\"']?([^\s`\"']+)"
)
PLACEHOLDER_VALUES = {
    "your-api-key",
    "your_api_key",
    "change-me",
    "changeme",
    "example",
    "placeholder",
    "<value>",
}
FORBIDDEN_PROJECT_NAMES = ("open-youth-policy",)


def relative(path: Path, root: Path) -> str:
    """Return a stable repository-relative path for diagnostics."""

    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def documentation_files(root: Path) -> list[Path]:
    """Return the Markdown files governed by the documentation system."""

    files = list((root / "docs").rglob("*.md"))
    files.extend(path for path in (root / "README.md", root / "CHANGELOG.md") if path.exists())
    return sorted(set(files))


def check_required_files(root: Path) -> list[str]:
    errors: list[str] = []
    for item in REQUIRED_FILES:
        if not (root / item).is_file():
            errors.append(f"required file is missing: {item}")
    return errors


def link_target(link: str) -> str:
    """Extract the path portion from a Markdown link target."""

    target = link.strip().split(maxsplit=1)[0].strip("<>")
    return unquote(target.split("#", maxsplit=1)[0])


def check_markdown_links(root: Path, files: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK.finditer(text):
            raw_target = match.group(1).strip()
            if raw_target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = link_target(raw_target)
            if not target:
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                errors.append(
                    f"{relative(path, root)}: broken link target: {raw_target}"
                )
    return errors


def check_forbidden_names(root: Path, files: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8").lower()
        for name in FORBIDDEN_PROJECT_NAMES:
            if name in text:
                errors.append(
                    f"{relative(path, root)}: legacy project name found: {name}"
                )
    return errors


def check_secret_assignments(root: Path, files: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for match in SECRET_ASSIGNMENT.finditer(text):
            value = match.group(2).strip().lower()
            if not value or value in PLACEHOLDER_VALUES:
                continue
            line = text.count("\n", 0, match.start()) + 1
            errors.append(
                f"{relative(path, root)}:{line}: possible secret value assigned "
                f"to {match.group(1)}"
            )
    return errors


def check_empty_docs(root: Path) -> list[str]:
    errors: list[str] = []
    docs = root / "docs"
    if not docs.is_dir():
        return ["docs directory is missing"]
    for path in docs.rglob("*"):
        if path.is_file() and path.stat().st_size == 0:
            errors.append(f"empty documentation file: {relative(path, root)}")
        elif path.is_dir() and not any(path.iterdir()):
            errors.append(f"empty documentation directory: {relative(path, root)}")
    return errors


def has_heading(text: str, heading: str) -> bool:
    return re.search(rf"(?m)^## {re.escape(heading)}\s*$", text) is not None


def first_status(text: str) -> str | None:
    match = re.search(r"(?m)^- 상태:\s*([a-z-]+)\s*$", text)
    return match.group(1) if match else None


def forest_name_from_plan(path: Path) -> str:
    return re.sub(r"^\d+_", "", path.stem)


def check_forest_documents(root: Path) -> list[str]:
    errors: list[str] = []
    plan_dir = root / "docs/development/develop_plan"
    note_dir = root / "docs/development/development_notes"
    plans = sorted(plan_dir.glob("[0-9][0-9]_*.md"))
    notes = {
        path.stem: path
        for path in note_dir.glob("*.md")
        if path.name.lower() != "readme.md"
    }

    if not plans:
        errors.append("no numbered Forest develop plan exists")

    plan_names: set[str] = set()
    for plan in plans:
        name = forest_name_from_plan(plan)
        plan_names.add(name)
        text = plan.read_text(encoding="utf-8")
        for heading in PLAN_HEADINGS:
            if not has_heading(text, heading):
                errors.append(
                    f"{relative(plan, root)}: missing required heading: {heading}"
                )
        status = first_status(text)
        if status not in ALLOWED_STATUSES:
            errors.append(
                f"{relative(plan, root)}: missing or invalid Forest status: {status}"
            )
        if status == "completed" and re.search(
            r"(?m)^- 상태:\s*(pending|in-progress)\s*$", text
        ):
            errors.append(
                f"{relative(plan, root)}: completed Forest has unfinished Slice"
            )
        if name not in notes:
            errors.append(
                f"{relative(plan, root)}: matching development note is missing"
            )

    for name, note in notes.items():
        text = note.read_text(encoding="utf-8")
        for heading in NOTE_HEADINGS:
            if not has_heading(text, heading):
                errors.append(
                    f"{relative(note, root)}: missing required heading: {heading}"
                )
        status = first_status(text)
        if status not in ALLOWED_STATUSES:
            errors.append(
                f"{relative(note, root)}: missing or invalid Forest status: {status}"
            )
        if status == "completed" and re.search(
            r"(?m)^\|\s*D\d+\s*\|\s*(pending|in-progress)\s*\|", text
        ):
            errors.append(
                f"{relative(note, root)}: completed Forest has unfinished Slice"
            )
        if name not in plan_names:
            errors.append(
                f"{relative(note, root)}: matching numbered develop plan is missing"
            )

    return errors


def validate_repository(root: Path) -> list[str]:
    root = root.resolve()
    files = documentation_files(root)
    checks = (
        check_required_files(root),
        check_markdown_links(root, files),
        check_forbidden_names(root, files),
        check_secret_assignments(root, files),
        check_empty_docs(root),
        check_forest_documents(root),
    )
    return [error for result in checks for error in result]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the parent of scripts/)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors = validate_repository(args.root)
    if errors:
        print(f"Documentation validation failed ({len(errors)} error(s)):")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Documentation validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
