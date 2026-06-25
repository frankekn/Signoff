"""Small dependency-free utilities used throughout Signoff."""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .errors import ValidationError

PLACEHOLDER_RE = re.compile(r"(?:TODO|TBD|REPLACE_ME|<[^>]+>|\[fill[^\]]*\])", re.IGNORECASE)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ValidationError(f"cannot read required file {path}: {exc}") from exc
    return digest.hexdigest()


def atomic_write_text(path: Path, text: str, *, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{secrets.token_hex(4)}.tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    if mode is not None:
        tmp.chmod(mode)
    os.replace(tmp, path)


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"required JSON file is missing: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"invalid JSON file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"JSON root must be an object: {path}")
    return value


def require_keys(value: dict[str, Any], keys: Iterable[str], context: str) -> None:
    missing = [key for key in keys if key not in value]
    if missing:
        raise ValidationError(f"{context} is missing: {', '.join(missing)}")


def require_clean_text(value: Any, context: str, *, minimum: int = 1) -> str:
    if not isinstance(value, str) or len(value.strip()) < minimum:
        raise ValidationError(f"{context} must be non-empty text")
    if PLACEHOLDER_RE.search(value):
        raise ValidationError(f"{context} still contains a placeholder")
    return value.strip()


def unique_ids(items: list[dict[str, Any]], context: str) -> set[str]:
    result: set[str] = set()
    for index, item in enumerate(items):
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValidationError(f"{context}[{index}].id must be non-empty")
        if identifier in result:
            raise ValidationError(f"duplicate {context} id: {identifier}")
        result.add(identifier)
    return result


def normalize_relpath(value: str) -> str:
    path = value.replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    if not path or path.startswith("/") or path == ".." or path.startswith("../") or "/../" in path:
        raise ValidationError(f"path must stay inside the repository: {value}")
    return path


def matches_any(path: str, patterns: Iterable[str]) -> bool:
    normalized = path.replace("\\", "/")
    return any(fnmatch.fnmatchcase(normalized, pattern.replace("\\", "/")) for pattern in patterns)


def ensure_within(root: Path, candidate: Path) -> Path:
    root = root.resolve()
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValidationError(f"path escapes project root: {candidate}") from exc
    return candidate


def short_id(prefix: str, seed: str = "") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    suffix = sha256_text(seed + secrets.token_hex(4))[:8]
    return f"{prefix}-{stamp}-{suffix}"


def bounded_text(text: str, limit: int = 200_000) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    half = max(1, limit // 2)
    return text[:half] + "\n...<truncated by Signoff>...\n" + text[-half:], True
