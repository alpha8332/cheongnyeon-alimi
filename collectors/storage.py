"""Path-confined storage for runtime Raw documents."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import timezone
from pathlib import Path
from typing import Any

from collectors.raw import RawDocumentValidationError, RawPolicyDocument


DEFAULT_RAW_ROOT = Path("runtime/raw")


class RawStorageError(OSError):
    """A Raw document could not be stored or loaded safely."""


class RawDocumentStore:
    """Store immutable Raw envelopes below one configured runtime root."""

    def __init__(self, root: str | Path = DEFAULT_RAW_ROOT) -> None:
        self.root = Path(root).resolve()

    def path_for(self, document: RawPolicyDocument) -> Path:
        collected_date = document.collected_at.astimezone(timezone.utc).date()
        target = (
            self.root
            / document.source_id
            / document.document_role.value
            / f"{collected_date:%Y}"
            / f"{collected_date:%m}"
            / f"{collected_date:%d}"
            / f"{document.document_id}.json"
        )
        self._ensure_within_root(target)
        return target

    def save(self, document: RawPolicyDocument) -> Path:
        target = self.path_for(document)
        target.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_within_root(target.parent.resolve())
        if target.exists():
            raise RawStorageError("Raw document already exists")

        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=".raw-",
            suffix=".tmp",
            dir=target.parent,
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(file_descriptor, "wb") as temporary_file:
                temporary_file.write(document.to_json_bytes())
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.link(temporary_path, target)
        except FileExistsError:
            raise RawStorageError("Raw document already exists") from None
        except OSError:
            raise RawStorageError("Raw document could not be stored") from None
        finally:
            temporary_path.unlink(missing_ok=True)
        return target

    def load(self, path: str | Path) -> RawPolicyDocument:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        try:
            resolved = candidate.resolve(strict=True)
            self._ensure_within_root(resolved)
            value: Any = json.loads(resolved.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise RawDocumentValidationError(
                    "Raw storage envelope must be an object"
                )
            return RawPolicyDocument.from_dict(value)
        except (OSError, json.JSONDecodeError, RawDocumentValidationError):
            raise RawStorageError("Raw document could not be loaded") from None

    def _ensure_within_root(self, path: Path) -> None:
        try:
            path.resolve().relative_to(self.root)
        except ValueError:
            raise RawStorageError(
                "Raw storage path escapes the configured root"
            ) from None
