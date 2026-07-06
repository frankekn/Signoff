from __future__ import annotations

import unittest
from pathlib import Path


class WebSourceContractTests(unittest.TestCase):
    def test_artifact_panel_keeps_discard_available_after_artifact_is_sealed(self) -> None:
        source = Path(__file__).resolve().parents[1] / "apps" / "web" / "src" / "components" / "ArtifactPanel.tsx"
        text = source.read_text(encoding="utf-8")

        discard_index = text.index("Discard draft")
        save_index = text.index("Save changes")
        dirty_guard_index = text.rfind("{dirty && (", 0, discard_index)
        editable_save_guard_index = text.rfind("{selected?.editable && (", 0, save_index)

        self.assertNotEqual(dirty_guard_index, -1)
        self.assertLess(dirty_guard_index, discard_index)
        self.assertLess(discard_index, editable_save_guard_index)
        self.assertLess(editable_save_guard_index, save_index)

    def test_source_cmd_launcher_restores_caller_cwd(self) -> None:
        text = (Path(__file__).resolve().parents[1] / "traction.cmd").read_text(encoding="utf-8")
        self.assertIn("pushd", text.lower())
        self.assertIn("popd", text.lower())

    def test_source_ps_launcher_restores_caller_cwd(self) -> None:
        text = (Path(__file__).resolve().parents[1] / "traction.ps1").read_text(encoding="utf-8")
        self.assertIn("Push-Location", text)
        self.assertIn("Pop-Location", text)
        self.assertNotIn("Set-Location -LiteralPath $Runtime", text)

    def test_installed_cmd_launcher_template_restores_caller_cwd(self) -> None:
        text = (Path(__file__).resolve().parents[1] / "src" / "traction" / "installer.py").read_text(encoding="utf-8")
        cmd_start = text.index("CMD_LAUNCHER = r'''")
        cmd_end = text.index("'''", cmd_start + len("CMD_LAUNCHER = r'''"))
        cmd_launcher = text[cmd_start:cmd_end]
        self.assertIn("pushd", cmd_launcher.lower())
        self.assertIn("popd", cmd_launcher.lower())
