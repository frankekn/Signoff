#!/usr/bin/env python3
from __future__ import annotations

import sys
sys.dont_write_bytecode = True
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py", top_level_dir=str(ROOT))
result = unittest.TextTestRunner(verbosity=2).run(suite)
print(f"\nConformance: {result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} passed")
raise SystemExit(0 if result.wasSuccessful() else 1)
