#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md",
    "README.zh-TW.md",
    "INSTALL_FOR_AGENTS.md",
    "LICENSE",
    "pyproject.toml",
    "package.json",
    "package-lock.json",
    "install.sh",
    "install.ps1",
    "signoff",
    "signoff.cmd",
    "signoff.ps1",
    "src/signoff/cli.py",
    "src/signoff/web.py",
    "src/signoff/web_dist/index.html",
    "apps/web/src/main.tsx",
    "skills/signoff/SKILL.md",
    "skills/council/SKILL.md",
    "skills/roast/SKILL.md",
    "protocol/schemas/spec.schema.json",
    "tests/test_conformance.py",
    "tests/test_web.py",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


errors: list[str] = []
for relative in REQUIRED:
    if not (ROOT / relative).is_file():
        errors.append(f"missing required file: {relative}")

for path in ROOT.rglob("*"):
    if "node_modules" in path.parts or ".git" in path.parts:
        continue
    if path.name == "__MACOSX" or path.name.startswith("._"):
        errors.append(f"Finder artifact: {path.relative_to(ROOT)}")

git_probe = subprocess.run(
    ["git", "-C", str(ROOT), "rev-parse", "--is-inside-work-tree"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
)
is_git_repository = git_probe.returncode == 0 and git_probe.stdout.strip() == "true"

if is_git_repository:
    tracked_proc = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    for raw in tracked_proc.stdout.split(b"\0"):
        if not raw:
            continue
        relative = Path(raw.decode("utf-8", errors="surrogateescape"))
        if "__pycache__" in relative.parts or relative.suffix in {".pyc", ".pyo"}:
            errors.append(f"tracked generated cache: {relative}")
        if "node_modules" in relative.parts or ("apps" in relative.parts and "dist" in relative.parts):
            errors.append(f"tracked development build artifact: {relative}")

for skill in ("signoff", "council", "roast"):
    top = ROOT / "skills" / skill
    packaged = ROOT / "src" / "signoff" / "assets" / "skills" / skill
    top_files = {path.relative_to(top) for path in top.rglob("*") if path.is_file()}
    packaged_files = {path.relative_to(packaged) for path in packaged.rglob("*") if path.is_file()}
    if top_files != packaged_files:
        errors.append(f"packaged skill file set drift: {skill}")
    for relative in sorted(top_files & packaged_files):
        if digest(top / relative) != digest(packaged / relative):
            errors.append(f"packaged skill drift: {skill}/{relative}")

for path in sorted((ROOT / "src").rglob("*.py")) + sorted((ROOT / "scripts").glob("*.py")):
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    except (OSError, SyntaxError, UnicodeError) as exc:
        errors.append(f"Python syntax check failed: {path.relative_to(ROOT)}: {exc}")

try:
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    web_package = json.loads((ROOT / "apps" / "web" / "package.json").read_text(encoding="utf-8"))
    if package.get("version") != web_package.get("version"):
        errors.append("root and web package versions differ")
except (OSError, json.JSONDecodeError) as exc:
    errors.append(f"invalid package metadata: {exc}")

index_path = ROOT / "src" / "signoff" / "web_dist" / "index.html"
if index_path.is_file():
    index = index_path.read_text(encoding="utf-8")
    for asset in re.findall(r'(?:src|href)="(/assets/[^"]+)"', index):
        if not (ROOT / "src" / "signoff" / "web_dist" / asset.lstrip("/")).is_file():
            errors.append(f"packaged UI references missing asset: {asset}")

if os.name != "nt" and (ROOT / "signoff").is_file() and not os.access(ROOT / "signoff", os.X_OK):
    errors.append("signoff launcher is not executable")
if os.name != "nt" and (ROOT / "install.sh").is_file() and not os.access(ROOT / "install.sh", os.X_OK):
    errors.append("install.sh is not executable")

if is_git_repository:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "diff", "--check"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode == 2 or proc.stdout.strip():
        errors.append(proc.stdout.strip() or proc.stderr.strip())

if errors:
    print("Repository check failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)
print("Repository check passed")
