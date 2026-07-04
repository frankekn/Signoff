from __future__ import annotations

from pathlib import Path
from typing import Final, TypedDict

from .errors import StateError, ValidationError
from .state import mission_dir, read_mission_state, read_root_state
from .util import ensure_within
from .web_overview import editable_paths

TEXT_ARTIFACT_SUFFIXES: Final = {".json", ".jsonl", ".md", ".txt", ".diff", ".log"}


class ArtifactSummary(TypedDict):
    path: str
    name: str
    size: int
    editable: bool
    kind: str


def list_artifacts(project: Path, mission_id: str) -> list[ArtifactSummary]:
    base = mission_dir(project, mission_id)
    if not base.is_dir():
        raise ValidationError(f"unknown mission: {mission_id}")
    state = read_mission_state(project, mission_id)
    root = read_root_state(project)
    editable = editable_paths(project, state) if mission_id == root.get("active_mission_id") else set()
    artifacts: list[ArtifactSummary] = []
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_ARTIFACT_SUFFIXES:
            continue
        relative = path.relative_to(project).as_posix()
        artifacts.append(
            {
                "path": relative,
                "name": path.name,
                "size": path.stat().st_size,
                "editable": relative in editable,
                "kind": path.suffix.lower().lstrip("."),
            }
        )
    return artifacts


def safe_artifact_path(project: Path, relative: str) -> Path:
    normalized = relative.strip().replace("\\", "/")
    if not normalized.startswith(".signoff/missions/"):
        raise ValidationError("artifact path must stay inside .signoff/missions")
    candidate = ensure_within(project, project / normalized)
    missions_root = ensure_within(project, project / ".signoff" / "missions")
    try:
        candidate.relative_to(missions_root)
    except ValueError as exc:
        raise ValidationError("artifact path escapes the mission directory") from exc
    if candidate.suffix.lower() not in TEXT_ARTIFACT_SUFFIXES:
        raise ValidationError("unsupported artifact type")
    return candidate


def assert_editable_artifact(project: Path, relative: str) -> None:
    root = read_root_state(project)
    mission_id = root.get("active_mission_id")
    if not mission_id:
        raise StateError("there is no active mission")
    state = read_mission_state(project, mission_id)
    if relative not in editable_paths(project, state):
        raise StateError("this artifact is locked or generated in the current phase")
