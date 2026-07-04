"""Append-only, hash-chained local audit ledger."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import IntegrityError
from .util import atomic_write_text, canonical_json, now_utc, sha256_text


def _hash_record(record_without_hash: dict[str, Any]) -> str:
    return sha256_text(canonical_json(record_without_hash))


def read_and_verify(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    previous = "0" * 64
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise IntegrityError(f"cannot read ledger: {exc}") from exc
    for index, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise IntegrityError(f"ledger line {index} is invalid JSON") from exc
        if record.get("seq") != len(records) + 1:
            raise IntegrityError(f"ledger sequence break at line {index}")
        if record.get("prev_hash") != previous:
            raise IntegrityError(f"ledger previous-hash break at line {index}")
        claimed = record.get("hash")
        unsigned = dict(record)
        unsigned.pop("hash", None)
        actual = _hash_record(unsigned)
        if claimed != actual:
            raise IntegrityError(f"ledger hash mismatch at line {index}")
        previous = claimed
        records.append(record)
    return records


def append(path: Path, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    records = read_and_verify(path)
    previous = records[-1]["hash"] if records else "0" * 64
    unsigned = {
        "seq": len(records) + 1,
        "time": now_utc(),
        "type": event_type,
        "payload": payload,
        "prev_hash": previous,
    }
    record = {**unsigned, "hash": _hash_record(unsigned)}
    text = "" if not path.exists() else path.read_text(encoding="utf-8")
    if text and not text.endswith("\n"):
        text += "\n"
    text += json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
    atomic_write_text(path, text)
    return record
