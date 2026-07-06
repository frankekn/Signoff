from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from scripts.create_demo import create as create_demo
from traction.errors import StateError
from traction.installer import install
from traction.util import atomic_write_json, read_json

from tests.support import RepoFixture


def move_current_control_to_legacy(project: Path, run_id: str) -> Path:
    current_root = project / ".traction"
    legacy_root = project / ".signoff"
    mission_id = "mission-" + run_id.removeprefix("run-")
    mission_dir = legacy_root / "missions" / mission_id
    current_root.rename(legacy_root)
    runs_dir = legacy_root / "runs"
    missions_dir = legacy_root / "missions"
    runs_dir.rename(missions_dir)
    (missions_dir / run_id).rename(mission_dir)
    root = read_json(legacy_root / "state.json")
    root["active_mission_id"] = mission_id
    root["missions"] = [mission_id]
    root.pop("active_run_id", None)
    root.pop("runs", None)
    atomic_write_json(legacy_root / "state.json", root)
    state = read_json(mission_dir / "STATE.json")
    state["mission_id"] = mission_id
    state.pop("run_id", None)
    if "run_baseline" in state:
        state["mission_baseline"] = state.pop("run_baseline")
    atomic_write_json(mission_dir / "STATE.json", state)
    return legacy_root


class DemoSetupTests(unittest.TestCase):
    def test_demo_setup_reaches_active_slice_with_route_synthesis(self) -> None:
        with tempfile.TemporaryDirectory(prefix="traction-demo-test-") as tmp:
            project = create_demo(Path(tmp) / "demo")
            root = read_json(project / ".traction" / "state.json")
            run_id = root["active_run_id"]
            run_state = read_json(project / ".traction" / "runs" / run_id / "STATE.json")
            push = read_json(project / ".traction" / "runs" / run_id / "PUSH.json")

            self.assertEqual(run_state["phase"], "IMPLEMENTING")
            self.assertEqual(push["decision"]["route_synthesis"], "Use the shared app.py route and focused unittest as the demo implementation path.")


class LegacyMigrationTests(unittest.TestCase):
    def test_install_refuses_active_legacy_signoff_state_when_traction_exists(self) -> None:
        fx = RepoFixture()
        try:
            source_root = Path(__file__).resolve().parents[1]
            legacy_root = move_current_control_to_legacy(fx.project, fx.run_id)
            (fx.project / ".traction").mkdir()

            with self.assertRaisesRegex(StateError, "old ./signoff CLI"):
                install(fx.project, source_root)

            self.assertTrue(legacy_root.exists())
        finally:
            fx.close()

    def test_install_warns_for_terminal_legacy_signoff_state_when_traction_exists(self) -> None:
        fx = RepoFixture()
        try:
            source_root = Path(__file__).resolve().parents[1]
            fx.runtime.finish("stopped", note="done for test")
            legacy_root = move_current_control_to_legacy(fx.project, fx.run_id)
            (fx.project / ".traction").mkdir()
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                install(fx.project, source_root)

            self.assertIn("legacy .signoff/ exists alongside .traction/", stderr.getvalue())
            self.assertTrue(legacy_root.exists())
            self.assertTrue((fx.project / ".traction").is_dir())
        finally:
            fx.close()
