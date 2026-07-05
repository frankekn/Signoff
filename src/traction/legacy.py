from __future__ import annotations

import sys
from pathlib import Path
from typing import TypeAlias

from .errors import StateError
from .state import TERMINAL_PHASES
from .util import atomic_write_json, read_json, sha256_file

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]
LEGACY_LAUNCHERS = ("signoff", "signoff.cmd", "signoff.ps1")
LEGACY_SKILL_DIRS = (
    ".agents/skills/signoff",
    ".agents/skills/council",
    ".agents/skills/roast",
    ".claude/skills/signoff",
    ".claude/skills/council",
    ".claude/skills/roast",
    ".gemini/skills/signoff",
    ".gemini/skills/council",
    ".gemini/skills/roast",
)
LEGACY_SKILL_PREFIXES = tuple(f"{directory}/" for directory in LEGACY_SKILL_DIRS)


def migrate_legacy_control_root(project: Path) -> None:
    legacy = project / ".signoff"
    current = project / ".traction"
    if legacy.exists() and current.exists():
        _ensure_legacy_runs_are_terminal(legacy)
        print(
            "traction: warning: legacy .signoff/ exists alongside .traction/; leaving both in place",
            file=sys.stderr,
        )
        return
    if not legacy.exists():
        return
    _ensure_legacy_runs_are_terminal(legacy)
    _remove_legacy_installer_outputs(project, legacy)
    legacy.rename(current)
    _translate_legacy_control_state(current)


def _ensure_legacy_runs_are_terminal(legacy: Path) -> None:
    root_path = legacy / "state.json"
    if not root_path.is_file():
        return
    root = read_json(root_path)
    for mission_id in _legacy_mission_ids(root):
        state_path = legacy / "missions" / mission_id / "STATE.json"
        if not state_path.is_file():
            continue
        phase = read_json(state_path).get("phase")
        if phase not in TERMINAL_PHASES:
            raise StateError(
                "legacy .signoff run is still active in phase "
                f"{phase}; finish or stop it with the old ./signoff CLI before running ./traction install"
            )


def _translate_legacy_control_state(current: Path) -> None:
    root_path = current / "state.json"
    if not root_path.is_file():
        return
    root = read_json(root_path)
    mission_ids = _legacy_mission_ids(root)
    id_map = {mission_id: _run_id_for_mission(mission_id) for mission_id in mission_ids}
    _rename_legacy_run_dirs(current, id_map)
    for mission_id, run_id in id_map.items():
        state_path = current / "runs" / run_id / "STATE.json"
        if state_path.is_file():
            state = read_json(state_path)
            _translate_legacy_run_state(state, mission_id, run_id)
            atomic_write_json(state_path, state)
    active_mission_id = root.pop("active_mission_id", None)
    root["active_run_id"] = id_map.get(active_mission_id) if isinstance(active_mission_id, str) else None
    root["runs"] = [id_map[mission_id] for mission_id in mission_ids]
    root.pop("missions", None)
    atomic_write_json(root_path, root)


def _remove_legacy_installer_outputs(project: Path, legacy: Path) -> None:
    manifest_path = legacy / "install-manifest.json"
    if not manifest_path.is_file():
        return
    manifest = read_json(manifest_path)
    files = manifest.get("files")
    if not isinstance(files, dict):
        return
    for relative, expected_hash in files.items():
        if not isinstance(relative, str) or not isinstance(expected_hash, str):
            continue
        normalized = relative.replace("\\", "/")
        if normalized.startswith("/") or ".." in normalized.split("/"):
            continue
        if normalized not in LEGACY_LAUNCHERS and not normalized.startswith(LEGACY_SKILL_PREFIXES):
            continue
        candidate = project / normalized
        if candidate.is_file() and sha256_file(candidate) == expected_hash:
            candidate.unlink()
    for relative in sorted(LEGACY_SKILL_DIRS, key=len, reverse=True):
        directory = project / relative
        if not directory.is_dir():
            continue
        for child in sorted((path for path in directory.rglob("*") if path.is_dir()), key=lambda path: len(path.parts), reverse=True):
            if not any(child.iterdir()):
                child.rmdir()
        if not any(directory.iterdir()):
            directory.rmdir()


def _legacy_mission_ids(root: JsonObject) -> list[str]:
    mission_ids: list[str] = []
    missions = root.get("missions")
    if isinstance(missions, list):
        mission_ids.extend(mission_id for mission_id in missions if isinstance(mission_id, str))
    active_mission_id = root.get("active_mission_id")
    if isinstance(active_mission_id, str) and active_mission_id not in mission_ids:
        mission_ids.append(active_mission_id)
    return mission_ids


def _run_id_for_mission(mission_id: str) -> str:
    return "run-" + mission_id.removeprefix("mission-")


def _rename_legacy_run_dirs(current: Path, id_map: dict[str, str]) -> None:
    missions = current / "missions"
    runs = current / "runs"
    if not missions.exists():
        return
    if runs.exists():
        raise StateError("cannot migrate legacy .signoff: both missions/ and runs/ exist")
    missions.rename(runs)
    for mission_id, run_id in id_map.items():
        source = runs / mission_id
        target = runs / run_id
        if source.exists():
            source.rename(target)
            council = target / "COUNCIL.json"
            push = target / "PUSH.json"
            if council.is_file() and not push.exists():
                council.rename(push)


def _translate_legacy_run_state(state: JsonObject, mission_id: str, run_id: str) -> None:
    state["run_id"] = run_id
    state.pop("mission_id", None)
    mission_baseline = state.pop("mission_baseline", None)
    if isinstance(mission_baseline, str):
        state["run_baseline"] = mission_baseline
    council_first_slice = state.pop("council_first_slice", None)
    if isinstance(council_first_slice, str):
        state["push_first_slice"] = council_first_slice
    lock = state.get("lock")
    if isinstance(lock, dict):
        _translate_legacy_lock(lock, mission_id, run_id)
    lock_history = state.get("lock_history")
    if isinstance(lock_history, list):
        for item in lock_history:
            if isinstance(item, dict):
                _translate_legacy_lock(item, mission_id, run_id)


def _translate_legacy_lock(lock: JsonObject, mission_id: str, run_id: str) -> None:
    if lock.get("mission_id") == mission_id:
        lock["run_id"] = run_id
        lock.pop("mission_id", None)
    council_sha256 = lock.pop("council_sha256", None)
    if isinstance(council_sha256, str):
        lock["push_sha256"] = council_sha256
    council_result = lock.pop("council_result", None)
    if isinstance(council_result, dict):
        lock["push_result"] = council_result
