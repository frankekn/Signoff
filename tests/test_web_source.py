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
