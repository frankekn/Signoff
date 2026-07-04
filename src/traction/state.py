"""Repository-local run state and lock integrity."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import IntegrityError, StateError, ValidationError
from .ledger import read_and_verify
from .util import atomic_write_json, read_json, sha256_file

CONTROL_DIR = ".traction"
ROOT_STATE = "state.json"
TERMINAL_PHASES = {"DONE", "STOPPED", "PIVOT", "BLOCKED"}


def control_root(project: Path) -> Path:
    return project / CONTROL_DIR


def root_state_path(project: Path) -> Path:
    return control_root(project) / ROOT_STATE


def run_dir(project: Path, run_id: str) -> Path:
    return control_root(project) / "runs" / run_id


def run_state_path(project: Path, run_id: str) -> Path:
    return run_dir(project, run_id) / "STATE.json"


def ledger_path(project: Path, run_id: str) -> Path:
    return run_dir(project, run_id) / "LEDGER.jsonl"


def read_root_state(project: Path) -> dict[str, Any]:
    path = root_state_path(project)
    if not path.exists():
        return {"schema_version": 1, "active_run_id": None, "runs": []}
    data = read_json(path)
    if data.get("schema_version") != 1:
        raise ValidationError("unsupported .traction/state.json schema_version")
    if not isinstance(data.get("runs"), list):
        raise ValidationError(".traction/state.json runs must be a list")
    return data


def write_root_state(project: Path, data: dict[str, Any]) -> None:
    atomic_write_json(root_state_path(project), data)


def read_run_state(project: Path, run_id: str) -> dict[str, Any]:
    data = read_json(run_state_path(project, run_id))
    if data.get("schema_version") != 1 or data.get("run_id") != run_id:
        raise ValidationError("invalid run STATE.json")
    read_and_verify(ledger_path(project, run_id))
    return data


def write_run_state(project: Path, state: dict[str, Any]) -> None:
    atomic_write_json(run_state_path(project, state["run_id"]), state)


def active_run(project: Path, *, required: bool = True) -> tuple[dict[str, Any], dict[str, Any]] | tuple[None, None]:
    root = read_root_state(project)
    run_id = root.get("active_run_id")
    if not run_id:
        if required:
            raise StateError("there is no active run; run ./traction start \"<outcome>\"")
        return None, None
    return root, read_run_state(project, run_id)


def require_phase(state: dict[str, Any], allowed: set[str] | tuple[str, ...] | list[str]) -> None:
    if state.get("phase") not in set(allowed):
        expected = ", ".join(sorted(set(allowed)))
        raise StateError(f"illegal action in phase {state.get('phase')}; expected one of: {expected}")


def verify_lock(project: Path, state: dict[str, Any]) -> dict[str, str]:
    lock = state.get("lock")
    if not isinstance(lock, dict):
        raise IntegrityError("run is not locked")
    base = run_dir(project, state["run_id"])
    mapping = {
        "goal": base / "GOAL.txt",
        "charter": base / "CHARTER.md",
        "spec": base / "SPEC.json",
        "push": base / "PUSH.json",
    }
    actual = {name: sha256_file(path) for name, path in mapping.items()}
    for name, digest in actual.items():
        if lock.get(f"{name}_sha256") != digest:
            raise IntegrityError(f"locked {name} hash mismatch; use a recorded Push pivot instead of editing it")
    lock_path = base / "LOCK.json"
    if sha256_file(lock_path) != state.get("lock_file_sha256"):
        raise IntegrityError("LOCK.json hash mismatch")
    return actual


def current_iteration_dir(project: Path, state: dict[str, Any]) -> Path:
    current = state.get("current")
    if not isinstance(current, dict):
        raise StateError("there is no active slice")
    return run_dir(project, state["run_id"]) / "iterations" / f"{current['iteration']:04d}"
