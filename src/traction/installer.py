"""Repository-local, idempotent installation for coding agents."""
from __future__ import annotations

import shutil
from pathlib import Path

from .errors import TractionError
from .legacy import migrate_legacy_control_root
from .util import atomic_write_json, atomic_write_text, now_utc, sha256_file

START = "<!-- traction:managed:start -->"
END = "<!-- traction:managed:end -->"
LEGACY_START = "<!-- signoff:managed:start -->"
LEGACY_END = "<!-- signoff:managed:end -->"
MANAGED_MARKERS = ((START, END), (LEGACY_START, LEGACY_END))
MANAGED_BLOCK = f"""{START}
## Traction

This repository uses the local Traction control plane.

1. Read `.agents/skills/traction/SKILL.md` before changing product code.
2. Run `./traction status` and obey the single action returned by `./traction next`.
3. Do not edit locked artifacts or generated receipts.
4. Builder, reviewers, and lead judge must use distinct real contexts.
5. A completion claim requires executable evidence and the deterministic gate.
{END}
"""

POSIX_LAUNCHER = r'''#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
RUNTIME="$ROOT/.traction/runtime"
PYTHON=${PYTHON:-python3}
CALLER_CWD=$(pwd)
cd "$RUNTIME"
TRACTION_CALLER_CWD="$CALLER_CWD" PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$RUNTIME${PYTHONPATH:+:$PYTHONPATH}" exec "$PYTHON" -m traction --project "$ROOT" "$@"
'''

CMD_LAUNCHER = r'''@echo off
set "ROOT=%~dp0"
set "RUNTIME=%ROOT%.traction\runtime"
set "PYTHONDONTWRITEBYTECODE=1"
set "TRACTION_CALLER_CWD=%CD%"
cd /d "%RUNTIME%"
set "PYTHONPATH=%RUNTIME%;%PYTHONPATH%"
python -m traction --project "%ROOT%" %*
'''

POWERSHELL_LAUNCHER = r'''$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Runtime = Join-Path $Root ".traction\runtime"
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTHONPATH = "$Runtime;$env:PYTHONPATH"
$env:TRACTION_CALLER_CWD = (Get-Location).Path
Push-Location -LiteralPath $Runtime
try {
  python -m traction --project $Root @args
  exit $LASTEXITCODE
} finally {
  Pop-Location
}
'''


def find_source_root() -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "skills" / "traction" / "SKILL.md").is_file() and (parent / "src" / "traction").is_dir():
            return parent
    return None


def _replace_managed_block(path: Path) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    managed = _split_first_managed_block(existing)
    if managed:
        before, after = managed
        text = (
            _remove_managed_blocks(before).rstrip()
            + "\n\n"
            + MANAGED_BLOCK
            + _remove_managed_blocks(after).lstrip("\n")
        )
    else:
        text = existing.rstrip() + ("\n\n" if existing.strip() else "") + MANAGED_BLOCK
    atomic_write_text(path, text if text.endswith("\n") else text + "\n")


def _split_first_managed_block(text: str) -> tuple[str, str] | None:
    first: tuple[int, str, str] | None = None
    for start, end in MANAGED_MARKERS:
        start_index = text.find(start)
        if start_index == -1:
            continue
        if end not in text[start_index:]:
            continue
        if first is None or start_index < first[0]:
            first = (start_index, start, end)
    if first is None:
        return None
    _index, start, end = first
    before, rest = text.split(start, 1)
    _old, after = rest.split(end, 1)
    return before, after


def _remove_managed_blocks(text: str) -> str:
    for start, end in MANAGED_MARKERS:
        while start in text:
            before, rest = text.split(start, 1)
            if end not in rest:
                break
            _old, after = rest.split(end, 1)
            text = before.rstrip() + "\n\n" + after.lstrip("\n")
    return text


def _copy_tree(source: Path, destination: Path) -> list[Path]:
    copied: list[Path] = []
    destination.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if "__pycache__" in relative.parts or path.suffix in {".pyc", ".pyo"} or path.name == ".DS_Store":
            continue
        target = destination / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            copied.append(target)
    return copied


def install(project: Path, source_root: Path | None = None) -> dict[str, str | int | list[str]]:
    project = project.resolve()
    migrate_legacy_control_root(project)
    source_root = source_root or find_source_root()
    package_source = Path(__file__).resolve().parent
    skills_source: Path | None = None
    if source_root and (source_root / "skills").is_dir():
        skills_source = source_root / "skills"
    elif (Path(__file__).resolve().parent / "assets" / "skills" / "traction" / "SKILL.md").is_file():
        skills_source = Path(__file__).resolve().parent / "assets" / "skills"
    elif (project / ".agents" / "skills" / "traction" / "SKILL.md").is_file():
        skills_source = project / ".agents" / "skills"
    else:
        raise TractionError("cannot locate the bundled Traction and loop skills")

    written: list[Path] = []
    runtime_destination = project / ".traction" / "runtime" / "traction"
    if package_source.resolve() != runtime_destination.resolve():
        if runtime_destination.exists():
            shutil.rmtree(runtime_destination)
        written.extend(_copy_tree(package_source, runtime_destination))

    for host_dir in (project / ".agents" / "skills", project / ".claude" / "skills", project / ".gemini" / "skills"):
        for skill_name in ("traction", "loop"):
            source = skills_source / skill_name
            destination = host_dir / skill_name
            if destination.exists():
                shutil.rmtree(destination)
            written.extend(_copy_tree(source, destination))

    launchers = {
        project / "traction": (POSIX_LAUNCHER, 0o755),
        project / "traction.cmd": (CMD_LAUNCHER, None),
        project / "traction.ps1": (POWERSHELL_LAUNCHER, None),
    }
    for path, (content, mode) in launchers.items():
        atomic_write_text(path, content, mode=mode)
        written.append(path)

    for name in ("AGENTS.md", "CLAUDE.md", "GEMINI.md"):
        path = project / name
        _replace_managed_block(path)
        written.append(path)

    manifest_path = project / ".traction" / "install-manifest.json"
    manifest_files = {
        str(path.relative_to(project)).replace("\\", "/"): sha256_file(path)
        for path in sorted(set(written))
        if path.is_file()
    }
    manifest = {
        "schema_version": 1,
        "installed_at": now_utc(),
        "source": str(source_root) if source_root else "installed-runtime",
        "files": manifest_files,
    }
    atomic_write_json(manifest_path, manifest)
    return {
        "status": "installed",
        "project": str(project),
        "runtime": str(runtime_destination.relative_to(project)),
        "skills": ["traction", "loop"],
        "managed_files": len(manifest_files),
        "next": "Run ./traction doctor, then ./traction start \"<the user’s exact outcome>\".",
    }
