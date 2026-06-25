"""Command-line interface for Signoff."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .errors import SignoffError
from .installer import find_source_root, install
from .runtime import Runtime


def _emit(value: Any, *, plain: bool = False) -> None:
    if plain and isinstance(value, str):
        print(value)
    else:
        print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="signoff",
        description="Spec-locked, evidence-driven engineering loops for coding agents.",
    )
    parser.add_argument("--project", default=".", help="target Git repository (default: current directory)")
    parser.add_argument("--version", action="version", version=f"Signoff {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("install", help="install Signoff locally into the target repository")

    ui = sub.add_parser("ui", help="open the local control and observability UI")
    ui.add_argument("--host", default="127.0.0.1", help="bind host (default: 127.0.0.1)")
    ui.add_argument("--port", type=int, default=8765, help="bind port (default: 8765; use 0 for any free port)")
    ui.add_argument("--no-open", action="store_true", help="do not open a browser automatically")
    sub.add_parser("doctor", help="check prerequisites and mission integrity")

    start = sub.add_parser("start", help="start a mission from the exact user-visible outcome")
    start.add_argument("goal")

    sub.add_parser("prepare-council", help="validate the draft and create the shared Council packet")
    sub.add_parser("lock", help="validate Council and hash-lock goal, charter, and spec")
    sub.add_parser("prepare-slice", help="create one bounded CONTRACT.json template")
    sub.add_parser("slice", help="validate and activate the current iteration contract")
    sub.add_parser("check-scope", help="show path, file, and changed-line budget status")
    sub.add_parser("verify", help="execute the locked verification commands and seal receipts")

    roast_prepare = sub.add_parser("prepare-roast", help="create sealed read-only review packets")
    roast_prepare.add_argument("--reviewers", type=int, default=2)
    sub.add_parser("roast", help="validate independent reviews and lead judgment")

    finish = sub.add_parser("finish", help="close the current slice or mission through a guarded decision")
    finish.add_argument("decision", choices=["accepted", "done", "rework", "blocked", "stopped", "pivot"])
    finish.add_argument("--root-cause", default="")
    finish.add_argument("--note", default="")

    pivot = sub.add_parser("pivot", help="archive the old lock and return to draft after Council review")
    pivot.add_argument("--reason", required=True)

    sub.add_parser("status", help="show current mission, proof, scope, and next action")
    sub.add_parser("next", help="print the one legal next action")
    sub.add_parser("integrity", help="revalidate ledger, locks, receipts, and active scope")
    sub.add_parser("benchmark", help="run the repository's deterministic conformance suite")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project = Path(args.project).expanduser().resolve()
    runtime = Runtime(project)
    try:
        if args.command == "install":
            _emit(install(project, find_source_root()))
        elif args.command == "ui":
            from .web import serve

            serve(project, host=args.host, port=args.port, open_browser=not args.no_open)
        elif args.command == "doctor":
            result = runtime.doctor()
            _emit(result)
            return 0 if result["status"] == "pass" else 2
        elif args.command == "start":
            _emit(runtime.start(args.goal))
        elif args.command == "prepare-council":
            _emit(runtime.prepare_council())
        elif args.command == "lock":
            _emit(runtime.lock())
        elif args.command == "prepare-slice":
            _emit(runtime.prepare_slice())
        elif args.command == "slice":
            _emit(runtime.activate_slice())
        elif args.command == "check-scope":
            result = runtime.check_scope()
            _emit(result)
            return 0 if result["status"] == "pass" else 2
        elif args.command == "verify":
            result = runtime.verify()
            _emit(result)
            return 0 if result["status"] == "pass" else 2
        elif args.command == "prepare-roast":
            _emit(runtime.prepare_roast(args.reviewers))
        elif args.command == "roast":
            _emit(runtime.roast())
        elif args.command == "finish":
            _emit(runtime.finish(args.decision, root_cause=args.root_cause, note=args.note))
        elif args.command == "pivot":
            _emit(runtime.authorize_pivot(args.reason))
        elif args.command == "status":
            _emit(runtime.status())
        elif args.command == "next":
            _emit(runtime.next_action(), plain=True)
        elif args.command == "integrity":
            _emit(runtime.integrity())
        elif args.command == "benchmark":
            source = find_source_root()
            if not source or not (source / "scripts" / "test.py").is_file():
                raise SignoffError("benchmark sources are not present in this local installation")
            proc = subprocess.run([sys.executable, str(source / "scripts" / "test.py")], cwd=source, check=False)
            return proc.returncode
        return 0
    except SignoffError as exc:
        print(f"signoff: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("signoff: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
