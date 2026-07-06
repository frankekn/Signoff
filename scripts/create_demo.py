#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from traction.installer import install  # noqa: E402
from traction.runtime import Runtime  # noqa: E402
from traction.util import atomic_write_json, read_json  # noqa: E402


def git(project: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(project), *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def create(destination: Path | None = None) -> Path:
    if destination is None:
        destination = Path(tempfile.mkdtemp(prefix="traction-demo-"))
    else:
        destination = destination.expanduser().resolve()
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir(parents=True)

    shutil.copytree(ROOT / "examples" / "demo-project", destination, dirs_exist_ok=True)
    git(destination, "init", "-q")
    git(destination, "config", "user.email", "demo@traction.local")
    git(destination, "config", "user.name", "Traction Demo")
    git(destination, "add", ".")
    git(destination, "commit", "-qm", "demo baseline")

    install(destination, ROOT)
    git(destination, "add", ".")
    git(destination, "commit", "-qm", "install Traction")
    runtime = Runtime(destination)
    goal = "Change greet() to return exactly hello world while preserving all unrelated behavior."
    runtime.start(goal)
    status = runtime.status()
    run_id = status["run_id"]
    run_path = destination / ".traction" / "runs" / run_id

    (run_path / "CHARTER.md").write_text(
        f"""# Run Charter

- Run: `{run_id}`
- Exact user outcome (immutable):

> {goal}

## User-visible success
Calling `greet()` returns exactly `hello world`.

## Hard constraints
Preserve unrelated behavior, repository history, and the public function signature.

## Non-goals
Do not add dependencies, rename files, or refactor unrelated code.

## Stop / pivot conditions
Stop if the focused unit test cannot serve as an executable oracle.

## Evidence standard
The focused unit test passes against a patch limited to `app.py`.
""",
        encoding="utf-8",
    )
    spec = read_json(run_path / "SPEC.json")
    spec["acceptance_criteria"][0]["observable"] = "Calling greet returns exactly the string hello world."
    spec["acceptance_criteria"][0]["oracle"]["description"] = "The focused unittest checks the exact returned string."
    spec["non_goals"] = ["Do not add dependencies or refactor unrelated code."]
    atomic_write_json(run_path / "SPEC.json", spec)

    runtime.prepare_push()
    push = read_json(run_path / "PUSH.json")
    for index, advisor in enumerate(push["advisors"], start=1):
        advisor["identity"] = {
            "participant_id": f"demo-advisor-{index}",
            "provider": "demo",
            "model": f"independent-{index}",
            "context_id": f"demo-context-{index}",
        }
        advisor["verdict"] = "PROCEED"
        advisor["route"] = "Change only app.py and prove the exact greeting with the focused unittest."
        advisor["falsifiable_criteria"] = [
            "The focused unittest passes after the minimal implementation change.",
        ]
        advisor["risk"] = "The requested behavior might already exist or the test may encode the wrong result."
        advisor["first_move"] = "Run the focused unittest before changing implementation code."
        advisor["cut"] = "Exclude all refactors and dependency changes."
    push["decision"]["verdict"] = "PROCEED"
    push["decision"]["rationale"] = "Both independent demo advisors support the same minimal route and executable oracle."
    push["decision"]["route_synthesis"] = "Use the shared app.py route and focused unittest as the demo implementation path."
    push["decision"]["first_slice"] = "Change only app.py and prove the exact greeting with unittest."
    push["decision"]["chair"] = {
        "participant_id": "demo-chair",
        "provider": "demo",
        "model": "chair",
        "context_id": "demo-chair-context",
    }
    atomic_write_json(run_path / "PUSH.json", push)
    runtime.lock()
    runtime.prepare_slice()

    state = runtime.status()
    iteration = int(state["current"]["iteration"])
    contract_path = run_path / "iterations" / f"{iteration:04d}" / "CONTRACT.json"
    contract = read_json(contract_path)
    contract["title"] = "Return the exact requested greeting."
    contract["builder"] = {
        "participant_id": "demo-builder",
        "provider": "your-coding-agent",
        "model": "local-session",
        "context_id": "demo-builder-context",
    }
    contract["allowed_paths"] = ["app.py", "test_app.py"]
    contract["forbidden_paths"] = [".git/**", ".traction/**"]
    contract["exempt_paths"] = ["test_*.py"]
    contract["budgets"] = {"production_files": 1, "changed_lines": 12}
    contract["verification"] = [
        {
            "id": "V-001",
            "command": [sys.executable, "-m", "unittest", "-v"],
            "timeout_seconds": 60,
            "working_directory": ".",
            "acceptance_ids": ["AC-001"],
        }
    ]
    contract["final"] = True
    atomic_write_json(contract_path, contract)
    runtime.activate_slice()
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a disposable Traction demo repository")
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    project = create(args.destination)
    print(json.dumps({"project": str(project), "phase": "IMPLEMENTING"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
