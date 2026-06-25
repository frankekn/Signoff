#!/usr/bin/env python3
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "apps" / "web" / "dist"
destination = ROOT / "src" / "signoff" / "web_dist"
if not (source / "index.html").is_file():
    raise SystemExit("apps/web/dist is missing; build the Vite app first")
if destination.exists():
    shutil.rmtree(destination)
shutil.copytree(source, destination)
print(f"copied {source.relative_to(ROOT)} -> {destination.relative_to(ROOT)}")
