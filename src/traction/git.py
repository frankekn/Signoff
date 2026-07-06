"""Git-backed baselines, patches, and scope accounting."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Iterable

from .errors import TractionError
from .util import matches_any

CONTROL_GLOBS = (
    ".traction/**",
    ".agents/skills/traction/**",
    ".agents/skills/loop/**",
    ".claude/skills/traction/**",
    ".claude/skills/loop/**",
    ".gemini/skills/traction/**",
    ".gemini/skills/loop/**",
    "traction",
    "traction.cmd",
    "traction.ps1",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
)


def _product_pathspecs() -> list[str]:
    return [".", *(f":(exclude){pattern}" for pattern in CONTROL_GLOBS)]


def run_git(project: Path, args: list[str], *, check: bool = True, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", "-C", str(project), *args],
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or f"exit {proc.returncode}"
        raise TractionError(f"git {' '.join(args)} failed: {detail}")
    return proc


def ensure_repository(project: Path, *, require_commit: bool = True) -> None:
    inside = run_git(project, ["rev-parse", "--is-inside-work-tree"], check=False)
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        raise TractionError(f"Traction requires a Git working tree: {project}")
    if require_commit:
        head_proc = run_git(project, ["rev-parse", "--verify", "HEAD"], check=False)
        if head_proc.returncode != 0:
            raise TractionError("Traction requires at least one Git commit so scope has a stable baseline")


def head(project: Path) -> str:
    ensure_repository(project)
    return run_git(project, ["rev-parse", "HEAD"]).stdout.strip()


def _line_set(text: str) -> set[str]:
    return {line.strip().replace("\\", "/") for line in text.splitlines() if line.strip()}


def changed_files(project: Path, baseline: str, *, include_control: bool = False) -> list[str]:
    ensure_repository(project)
    pathspecs = ["."] if include_control else _product_pathspecs()
    paths = _line_set(run_git(project, ["diff", "--name-only", "--relative", baseline, "--", *pathspecs]).stdout)
    paths.update(_line_set(run_git(project, ["ls-files", "--others", "--exclude-standard"]).stdout))
    result = sorted(paths)
    if include_control:
        return result
    return [path for path in result if not matches_any(path, CONTROL_GLOBS)]


def _untracked_patch(project: Path, path: str) -> str:
    candidate = project / path
    if not candidate.is_file():
        return ""
    proc = subprocess.run(
        ["git", "-C", str(project), "diff", "--no-index", "--binary", "--", os.devnull, path],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode not in (0, 1):
        raise TractionError(f"cannot create patch for untracked file {path}: {proc.stderr.strip()}")
    return proc.stdout


def patch(project: Path, baseline: str) -> str:
    tracked = run_git(project, ["diff", "--binary", "--no-ext-diff", baseline, "--", *_product_pathspecs()]).stdout
    untracked = _line_set(run_git(project, ["ls-files", "--others", "--exclude-standard"]).stdout)
    chunks = [tracked]
    for path in sorted(untracked):
        if not matches_any(path, CONTROL_GLOBS):
            chunks.append(_untracked_patch(project, path))
    return "".join(chunks)


def changed_line_count(project: Path, baseline: str, files: Iterable[str] | None = None) -> int:
    selected = set(files or changed_files(project, baseline))
    total = 0
    numstat = run_git(project, ["diff", "--numstat", baseline, "--", *_product_pathspecs()]).stdout
    tracked_seen: set[str] = set()
    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added, deleted, path = parts[0], parts[1], parts[-1].replace("\\", "/")
        tracked_seen.add(path)
        if path not in selected or matches_any(path, CONTROL_GLOBS):
            continue
        if added.isdigit():
            total += int(added)
        if deleted.isdigit():
            total += int(deleted)
    for path in selected - tracked_seen:
        candidate = project / path
        if candidate.is_file() and not matches_any(path, CONTROL_GLOBS):
            try:
                data = candidate.read_bytes()
                total += data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)
            except OSError:
                pass
    return total



def snapshot_commit(project: Path, message: str) -> str:
    """Create an unreachable commit for the exact working tree without touching HEAD/index.

    The temporary index lives under Git's own directory so it can never appear as a
    product-file change, even when TMP/TEMP points inside the target repository.
    """
    import secrets

    ensure_repository(project)
    git_dir_value = run_git(project, ["rev-parse", "--git-dir"]).stdout.strip()
    git_dir = Path(git_dir_value)
    if not git_dir.is_absolute():
        git_dir = project / git_dir
    temp_dir = git_dir.resolve() / "traction"
    temp_dir.mkdir(parents=True, exist_ok=True)
    index_path = temp_dir / f"index-{secrets.token_hex(8)}"
    env = os.environ.copy()
    env["GIT_INDEX_FILE"] = str(index_path)
    base = head(project)
    try:
        for args in (["read-tree", base], ["add", "-A", "--", "."]):
            proc = subprocess.run(
                ["git", "-C", str(project), *args],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if proc.returncode != 0:
                raise TractionError(f"cannot create Traction snapshot: {proc.stderr.strip() or proc.stdout.strip()}")
        tree_proc = subprocess.run(
            ["git", "-C", str(project), "write-tree"],
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if tree_proc.returncode != 0:
            raise TractionError(f"cannot write Traction snapshot tree: {tree_proc.stderr.strip()}")
        identity_env = env.copy()
        identity_env.update(
            {
                "GIT_AUTHOR_NAME": "Traction",
                "GIT_AUTHOR_EMAIL": "traction@local.invalid",
                "GIT_COMMITTER_NAME": "Traction",
                "GIT_COMMITTER_EMAIL": "traction@local.invalid",
            }
        )
        commit_proc = subprocess.run(
            ["git", "-C", str(project), "commit-tree", tree_proc.stdout.strip(), "-p", base, "-m", message],
            env=identity_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if commit_proc.returncode != 0:
            raise TractionError(f"cannot create Traction snapshot commit: {commit_proc.stderr.strip()}")
        return commit_proc.stdout.strip()
    finally:
        for candidate in (index_path, Path(str(index_path) + ".lock")):
            try:
                candidate.unlink()
            except FileNotFoundError:
                pass
