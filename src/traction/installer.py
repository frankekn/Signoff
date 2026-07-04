"""Repository-local, idempotent installation for coding agents."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .errors import TractionError
from .util import atomic_write_json, atomic_write_text, now_utc, sha256_file

START = "<!-- traction:managed:start -->"
END = "<!-- traction:managed:end -->"
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
PYTHON=${PYTHON:-python3}
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT/.traction/runtime${PYTHONPATH:+:$PYTHONPATH}" exec "$PYTHON" -m traction --project "$ROOT" "$@"
'''

CMD_LAUNCHER = r'''@echo off
set "ROOT=%~dp0"
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONPATH=%ROOT%.traction\runtime;%PYTHONPATH%"
python -m traction --project "%ROOT%" %*
'''

POWERSHELL_LAUNCHER = r'''$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTHONPATH = "$Root\.traction\runtime;$env:PYTHONPATH"
python -m traction --project $Root @args
'''


def find_source_root() -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "skills" / "traction" / "SKILL.md").is_file() and (parent / "src" / "traction").is_dir():
            return parent
    return None


def _replace_managed_block(path: Path) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if START in existing and END in existing:
        before, rest = existing.split(START, 1)
        _old, after = rest.split(END, 1)
        text = before.rstrip() + "\n\n" + MANAGED_BLOCK + after.lstrip("\n")
    else:
        text = existing.rstrip() + ("\n\n" if existing.strip() else "") + MANAGED_BLOCK
    atomic_write_text(path, text if text.endswith("\n") else text + "\n")


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


def install(project: Path, source_root: Path | None = None) -> dict[str, Any]:
    project = project.resolve()
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
    manifest = {
        "schema_version": 1,
        "installed_at": now_utc(),
        "source": str(source_root) if source_root else "installed-runtime",
        "files": {
            str(path.relative_to(project)).replace("\\", "/"): sha256_file(path)
            for path in sorted(set(written))
            if path.is_file()
        },
    }
    atomic_write_json(manifest_path, manifest)
    return {
        "status": "installed",
        "project": str(project),
        "runtime": str(runtime_destination.relative_to(project)),
        "skills": ["traction", "loop"],
        "managed_files": len(manifest["files"]),
        "next": "Run ./traction doctor, then ./traction start \"<the user’s exact outcome>\".",
    }
