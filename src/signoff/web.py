"""Local web UI and JSON API for Signoff.

The server deliberately uses only the Python standard library. The React UI is
compiled ahead of time and shipped as package data, so end users do not need
Node.js to run it.
"""
from __future__ import annotations

import json
import mimetypes
import os
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from . import __version__
from .errors import SignoffError, StateError, ValidationError
from .ledger import read_and_verify
from .runtime import Runtime
from .state import ledger_path, mission_dir, read_mission_state, read_root_state
from .util import atomic_write_text, ensure_within

MAX_BODY_BYTES = 2 * 1024 * 1024
TEXT_ARTIFACT_SUFFIXES = {".json", ".jsonl", ".md", ".txt", ".diff", ".log"}


def _allowed_actions(phase: str) -> list[dict[str, Any]]:
    actions: dict[str, list[dict[str, Any]]] = {
        "IDLE": [],
        "DRAFT": [
            {"id": "prepare_council", "label": "Send to Council", "tone": "primary"},
            {"id": "finish_stopped", "label": "Stop mission", "tone": "danger", "requiresNote": True},
        ],
        "COUNCIL": [
            {"id": "lock", "label": "Lock decision", "tone": "primary"},
            {"id": "finish_stopped", "label": "Stop mission", "tone": "danger", "requiresNote": True},
        ],
        "LOCKED": [
            {"id": "prepare_slice", "label": "Create next slice", "tone": "primary"},
            {"id": "finish_stopped", "label": "Stop mission", "tone": "danger", "requiresNote": True},
        ],
        "SLICE_DRAFT": [
            {"id": "activate_slice", "label": "Activate slice", "tone": "primary"},
        ],
        "IMPLEMENTING": [
            {"id": "check_scope", "label": "Check scope", "tone": "neutral"},
            {"id": "verify", "label": "Run verification", "tone": "primary"},
        ],
        "VERIFY_FAILED": [
            {"id": "check_scope", "label": "Check scope", "tone": "neutral"},
            {"id": "verify", "label": "Verify again", "tone": "primary"},
        ],
        "VERIFIED": [
            {"id": "prepare_roast", "label": "Prepare independent review", "tone": "primary"},
        ],
        "REVIEWING": [
            {"id": "roast", "label": "Seal review", "tone": "primary"},
        ],
        "REVIEWED": [
            {"id": "finish_done", "label": "Sign off", "tone": "primary"},
            {"id": "finish_accepted", "label": "Accept slice", "tone": "neutral"},
            {"id": "finish_rework", "label": "Rework", "tone": "danger", "requiresNote": True},
        ],
        "COUNCIL_REVIEW": [
            {"id": "pivot", "label": "Authorize pivot", "tone": "primary", "requiresNote": True},
            {"id": "finish_stopped", "label": "Stop mission", "tone": "danger", "requiresNote": True},
        ],
        "DONE": [],
        "STOPPED": [],
        "PIVOT": [],
        "BLOCKED": [],
    }
    return actions.get(phase, [])


def _editable_paths(project: Path, state: dict[str, Any]) -> set[str]:
    mission_id = state["mission_id"]
    base = mission_dir(project, mission_id)
    phase = state.get("phase")
    allowed: set[Path] = set()
    if phase == "DRAFT":
        allowed.update({base / "CHARTER.md", base / "SPEC.json"})
    elif phase == "COUNCIL":
        allowed.add(base / "COUNCIL.json")
    elif phase == "SLICE_DRAFT" and state.get("current"):
        iteration = int(state["current"]["iteration"])
        allowed.add(base / "iterations" / f"{iteration:04d}" / "CONTRACT.json")
    elif phase == "REVIEWING" and state.get("current"):
        iteration = int(state["current"]["iteration"])
        iteration_dir = base / "iterations" / f"{iteration:04d}"
        allowed.add(iteration_dir / "JUDGMENT.json")
        review_dir = iteration_dir / "reviews"
        if review_dir.is_dir():
            allowed.update(path for path in review_dir.glob("review-*.json") if path.is_file())
    return {str(path.relative_to(project)).replace(os.sep, "/") for path in allowed}


def _mission_summaries(project: Path) -> list[dict[str, Any]]:
    root = read_root_state(project)
    summaries: list[dict[str, Any]] = []
    for mission_id in reversed(root.get("missions", [])):
        try:
            state = read_mission_state(project, mission_id)
            goal_path = mission_dir(project, mission_id) / "GOAL.txt"
            goal = goal_path.read_text(encoding="utf-8").strip() if goal_path.is_file() else ""
            summaries.append(
                {
                    "missionId": mission_id,
                    "goal": goal,
                    "phase": state.get("phase", "UNKNOWN"),
                    "revision": state.get("revision", 1),
                    "iteration": state.get("iteration", 0),
                    "updatedAt": state.get("updated_at"),
                    "active": mission_id == root.get("active_mission_id"),
                }
            )
        except SignoffError as exc:
            summaries.append(
                {
                    "missionId": mission_id,
                    "goal": "",
                    "phase": "INVALID",
                    "error": str(exc),
                    "active": mission_id == root.get("active_mission_id"),
                }
            )
    return summaries


def build_overview(project: Path, runtime: Runtime) -> dict[str, Any]:
    status = runtime.status()
    phase = status.get("phase", "IDLE")
    mission_id = status.get("mission_id")
    goal = ""
    editable: set[str] = set()
    if mission_id:
        state = read_mission_state(project, mission_id)
        goal_path = mission_dir(project, mission_id) / "GOAL.txt"
        if goal_path.is_file():
            goal = goal_path.read_text(encoding="utf-8").strip()
        editable = _editable_paths(project, state)
    actions = _allowed_actions(phase)
    if phase == "REVIEWED" and not bool((status.get("current") or {}).get("final")):
        actions = [action for action in actions if action["id"] != "finish_done"]
    return {
        "product": "Signoff",
        "version": __version__,
        "project": str(project),
        "goal": goal,
        "status": status,
        "next": status.get("next", ""),
        "actions": actions,
        "editablePaths": sorted(editable),
        "missions": _mission_summaries(project),
    }



def _require_known_mission(project: Path, mission_id: str) -> str:
    root = read_root_state(project)
    if mission_id not in root.get("missions", []):
        raise ValidationError(f"unknown mission: {mission_id}")
    return mission_id


def _list_artifacts(project: Path, mission_id: str) -> list[dict[str, Any]]:
    base = mission_dir(project, mission_id)
    if not base.is_dir():
        raise ValidationError(f"unknown mission: {mission_id}")
    state = read_mission_state(project, mission_id)
    editable = _editable_paths(project, state)
    artifacts: list[dict[str, Any]] = []
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_ARTIFACT_SUFFIXES:
            continue
        relative = str(path.relative_to(project)).replace(os.sep, "/")
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


def _safe_artifact_path(project: Path, relative: str) -> Path:
    relative = relative.strip().replace("\\", "/")
    if not relative.startswith(".signoff/missions/"):
        raise ValidationError("artifact path must stay inside .signoff/missions")
    candidate = ensure_within(project, project / relative)
    missions_root = ensure_within(project, project / ".signoff" / "missions")
    try:
        candidate.relative_to(missions_root)
    except ValueError as exc:
        raise ValidationError("artifact path escapes the mission directory") from exc
    if candidate.suffix.lower() not in TEXT_ARTIFACT_SUFFIXES:
        raise ValidationError("unsupported artifact type")
    return candidate


def _action(runtime: Runtime, action: str, payload: dict[str, Any]) -> Any:
    if action == "prepare_council":
        return runtime.prepare_council()
    if action == "lock":
        return runtime.lock()
    if action == "prepare_slice":
        return runtime.prepare_slice()
    if action == "activate_slice":
        return runtime.activate_slice()
    if action == "check_scope":
        return runtime.check_scope()
    if action == "verify":
        return runtime.verify()
    if action == "prepare_roast":
        return runtime.prepare_roast(int(payload.get("reviewers", 2)))
    if action == "roast":
        return runtime.roast()
    if action == "finish_done":
        return runtime.finish("done", note=str(payload.get("note", "")))
    if action == "finish_accepted":
        return runtime.finish("accepted", note=str(payload.get("note", "")))
    if action == "finish_rework":
        return runtime.finish("rework", root_cause=str(payload.get("note", "")))
    if action == "finish_stopped":
        return runtime.finish("stopped", note=str(payload.get("note", "")))
    if action == "pivot":
        return runtime.authorize_pivot(str(payload.get("note", "")))
    raise ValidationError(f"unknown action: {action}")


class CourtHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], project: Path, static_root: Path):
        self.project = project.resolve()
        self.runtime = Runtime(self.project)
        self.static_root = static_root.resolve()
        self.mutation_lock = threading.Lock()
        super().__init__(address, CourtRequestHandler)


class CourtRequestHandler(BaseHTTPRequestHandler):
    server: CourtHTTPServer

    def log_message(self, fmt: str, *args: Any) -> None:
        if os.environ.get("SIGNOFF_QUIET") != "1":
            super().log_message(fmt, *args)

    def _json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, message: str) -> None:
        self._json(status, {"ok": False, "error": message})

    def _body(self) -> dict[str, Any]:
        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise ValidationError("invalid Content-Length") from exc
        if length < 0 or length > MAX_BODY_BYTES:
            raise ValidationError("request body is too large")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValidationError("request body must be valid JSON") from exc
        if not isinstance(value, dict):
            raise ValidationError("request body must be a JSON object")
        return value

    def _serve_static(self, parsed_path: str) -> None:
        if not self.server.static_root.is_dir():
            self._error(
                HTTPStatus.SERVICE_UNAVAILABLE,
                "web UI assets are missing; run npm run build:web from the Signoff source repository",
            )
            return
        route = unquote(parsed_path).lstrip("/") or "index.html"
        candidate = (self.server.static_root / route).resolve()
        try:
            candidate.relative_to(self.server.static_root)
        except ValueError:
            self._error(HTTPStatus.NOT_FOUND, "not found")
            return
        if not candidate.is_file():
            candidate = self.server.static_root / "index.html"
        if not candidate.is_file():
            self._error(HTTPStatus.NOT_FOUND, "not found")
            return
        body = candidate.read_bytes()
        content_type, _ = mimetypes.guess_type(candidate.name)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", (content_type or "application/octet-stream") + ("; charset=utf-8" if candidate.suffix in {".html", ".css", ".js"} else ""))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache" if candidate.name == "index.html" else "public, max-age=31536000, immutable")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; font-src 'self'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        try:
            if parsed.path == "/api/health":
                self._json(HTTPStatus.OK, {"ok": True, "product": "Signoff", "version": __version__})
                return
            if parsed.path == "/api/overview":
                self._json(HTTPStatus.OK, {"ok": True, "data": build_overview(self.server.project, self.server.runtime)})
                return
            if parsed.path == "/api/artifacts":
                mission_id = query.get("missionId", [""])[0]
                if not mission_id:
                    status = self.server.runtime.status()
                    mission_id = str(status.get("mission_id") or "")
                if not mission_id:
                    self._json(HTTPStatus.OK, {"ok": True, "data": []})
                    return
                mission_id = _require_known_mission(self.server.project, mission_id)
                self._json(HTTPStatus.OK, {"ok": True, "data": _list_artifacts(self.server.project, mission_id)})
                return
            if parsed.path == "/api/artifact":
                relative = query.get("path", [""])[0]
                path = _safe_artifact_path(self.server.project, relative)
                if not path.is_file():
                    raise ValidationError("artifact does not exist")
                content = path.read_text(encoding="utf-8")
                self._json(
                    HTTPStatus.OK,
                    {"ok": True, "data": {"path": relative, "content": content, "size": len(content.encode('utf-8'))}},
                )
                return
            if parsed.path == "/api/events":
                mission_id = query.get("missionId", [""])[0]
                if not mission_id:
                    status = self.server.runtime.status()
                    mission_id = str(status.get("mission_id") or "")
                if mission_id:
                    mission_id = _require_known_mission(self.server.project, mission_id)
                records = read_and_verify(ledger_path(self.server.project, mission_id)) if mission_id else []
                self._json(HTTPStatus.OK, {"ok": True, "data": records})
                return
            self._serve_static(parsed.path)
        except SignoffError as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))
        except OSError as exc:
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        try:
            payload = self._body()
            with self.server.mutation_lock:
                if parsed.path == "/api/missions":
                    goal = str(payload.get("goal", ""))
                    result = self.server.runtime.start(goal)
                    self._json(HTTPStatus.CREATED, {"ok": True, "data": result})
                    return
                if parsed.path == "/api/action":
                    action = str(payload.get("action", ""))
                    result = _action(self.server.runtime, action, payload)
                    self._json(HTTPStatus.OK, {"ok": True, "data": result})
                    return
            self._error(HTTPStatus.NOT_FOUND, "not found")
        except SignoffError as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))
        except (TypeError, ValueError) as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))
        except OSError as exc:
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def do_PUT(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        try:
            if parsed.path != "/api/artifact":
                self._error(HTTPStatus.NOT_FOUND, "not found")
                return
            payload = self._body()
            relative = str(payload.get("path", ""))
            content = payload.get("content")
            if not isinstance(content, str):
                raise ValidationError("content must be text")
            path = _safe_artifact_path(self.server.project, relative)
            root = read_root_state(self.server.project)
            mission_id = root.get("active_mission_id")
            if not mission_id:
                raise StateError("there is no active mission")
            state = read_mission_state(self.server.project, mission_id)
            if relative not in _editable_paths(self.server.project, state):
                raise StateError("this artifact is locked or generated in the current phase")
            if path.suffix == ".json":
                try:
                    parsed_json = json.loads(content)
                except json.JSONDecodeError as exc:
                    raise ValidationError(f"invalid JSON: {exc}") from exc
                content = json.dumps(parsed_json, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            with self.server.mutation_lock:
                atomic_write_text(path, content if content.endswith("\n") else content + "\n")
            self._json(HTTPStatus.OK, {"ok": True, "data": {"path": relative, "saved": True}})
        except SignoffError as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))
        except OSError as exc:
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))


def create_server(project: Path, host: str = "127.0.0.1", port: int = 8765, static_root: Path | None = None) -> CourtHTTPServer:
    root = static_root or (Path(__file__).resolve().parent / "web_dist")
    return CourtHTTPServer((host, port), project, root)


def serve(project: Path, host: str = "127.0.0.1", port: int = 8765, *, open_browser: bool = True) -> None:
    server = create_server(project, host=host, port=port)
    actual_host, actual_port = server.server_address[:2]
    url_host = "127.0.0.1" if actual_host in {"0.0.0.0", "::"} else actual_host
    url = f"http://{url_host}:{actual_port}"
    print(f"Signoff UI: {url}")
    print(f"Project: {project.resolve()}")
    if open_browser:
        threading.Timer(0.25, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("\nSignoff UI stopped")
    finally:
        server.server_close()
