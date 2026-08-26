"""Validate the published cheongnyeon-alimi documentation."""

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
    "docs/product/README.md",
    "docs/architecture/README.md",
    "docs/api/README.md",
    "docs/data/README.md",
    "docs/development/README.md",
    "docs/governance/README.md",
    "docs/governance/documentation_policy.md",
    "docs/operations/README.md",
    "docs/troubleshooting/README.md",
    "docs/contest/README.md",
    "docs/contest/open_source_submission_checklist.md",
)

MARKDOWN_LINK = re.compile(r"!?\[[^\]]*]\(([^)]+)\)")
SECRET_ASSIGNMENT = re.compile(
    r"(?im)\b("
    r"YOUTHCENTER_API_KEY|BOKJIRO_API_KEY|API_KEY|SECRET_KEY|ACCESS_TOKEN|"
    r"ADMIN_PIN_HASH|ADMIN_TOKEN_SECRET|PRIVATE_KEY|PASSWORD"
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
    "<sha256-of-four-digit-pin>",
    "<random-secret>",
}
FORBIDDEN_PROJECT_NAMES = ("open-youth-policy",)


def relative(path: Path, root: Path) -> str:
    """Return a stable repository-relative path for diagnostics."""

    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def documentation_files(root: Path) -> list[Path]:
    """Return published Markdown files governed by the documentation system."""

    files = list((root / "docs").rglob("*.md"))
    files.extend(
        path
        for path in (root / "README.md", root / "CHANGELOG.md")
        if path.exists()
    )
    return sorted(set(files))


def check_required_files(root: Path) -> list[str]:
    return [
        f"required file is missing: {item}"
        for item in REQUIRED_FILES
        if not (root / item).is_file()
    ]


def link_target(link: str) -> str:
    """Extract the local path portion from a Markdown link target."""

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
            if target and not (path.parent / target).resolve().exists():
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
    docs = root / "docs"
    if not docs.is_dir():
        return ["docs directory is missing"]
    return [
        f"empty documentation file: {relative(path, root)}"
        for path in docs.rglob("*")
        if path.is_file() and path.stat().st_size == 0
    ]


def validate_repository(root: Path) -> list[str]:
    root = root.resolve()
    files = documentation_files(root)
    checks = (
        check_required_files(root),
        check_markdown_links(root, files),
        check_forbidden_names(root, files),
        check_secret_assignments(root, files),
        check_empty_docs(root),
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
    errors = validate_repository(parse_args().root)
    if errors:
        print(f"Documentation validation failed ({len(errors)} error(s)):")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Documentation validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
