#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
VERSION = "0.1.0-alpha.1"
EXCLUDED_PARTS = {
    ".git",
    ".traction",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}

DIST.mkdir(exist_ok=True)
archive = DIST / f"traction-{VERSION}.zip"
if archive.exists():
    archive.unlink()
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.is_file() and path.suffix not in EXCLUDED_SUFFIXES:
            info = zipfile.ZipInfo.from_file(path, Path(f"traction-{VERSION}") / relative)
            info.compress_type = zipfile.ZIP_DEFLATED
            with path.open("rb") as source:
                zf.writestr(info, source.read(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
sha = hashlib.sha256(archive.read_bytes()).hexdigest()
checksum = DIST / "SHA256SUMS.txt"
checksum.write_text(f"{sha}  {archive.name}\n", encoding="utf-8")
print(archive)
print(checksum)
