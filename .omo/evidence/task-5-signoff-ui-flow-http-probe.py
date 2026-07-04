from __future__ import annotations

import json
import subprocess
import sys
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import signoff
from signoff.web import create_server
from tests.support import RepoFixture


STATIC_ROOT = Path(signoff.__file__).resolve().parent / "web_dist"


@contextmanager
def served(fx: RepoFixture) -> Iterator[str]:
    server = create_server(fx.project, host="127.0.0.1", port=0, static_root=STATIC_ROOT)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def curl(url: str) -> str:
    command = ["curl", "-i", "--silent", "--show-error", url]
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    return "$ " + " ".join(command) + "\n" + result.stdout + result.stderr


def section(name: str, body: str) -> str:
    return f"\n===== {name} =====\n{body.rstrip()}\n"


def main() -> int:
    out: list[str] = ["# Task 5 HTTP proof\n"]

    fx = RepoFixture()
    try:
        with served(fx) as base:
            out.append(section("DRAFT unknown proof", curl(f"{base}/api/overview")))
            out.append(section("unknown inspectMissionId controlled 400", curl(f"{base}/api/overview?inspectMissionId=missing-mission")))
    finally:
        fx.close()

    fx = RepoFixture()
    try:
        fx.lock()
        fx.activate(command=["git", "grep", "-F", "-q", "definitely-not-present", "--", "app.py"])
        fx.runtime.verify()
        with served(fx) as base:
            out.append(section("VERIFY_FAILED failed command", curl(f"{base}/api/overview")))
    finally:
        fx.close()

    fx = RepoFixture()
    try:
        fx.lock()
        iteration_dir = fx.passing_evidence(final=False)
        fx.fill_roast(iteration_dir)
        fx.runtime.roast()
        with served(fx) as base:
            out.append(section("REVIEWED PASS nonfinal", curl(f"{base}/api/overview")))
    finally:
        fx.close()

    fx = RepoFixture()
    try:
        fx.lock()
        iteration_dir = fx.passing_evidence(final=True)
        fx.fill_roast(iteration_dir)
        fx.runtime.roast()
        with served(fx) as base:
            out.append(section("REVIEWED PASS final", curl(f"{base}/api/overview")))
    finally:
        fx.close()

    fx = RepoFixture()
    try:
        old_mission_id = fx.mission_id
        fx.lock()
        iteration_dir = fx.passing_evidence(final=True)
        fx.fill_roast(iteration_dir)
        fx.runtime.roast()
        fx.runtime.finish("done")
        fx.runtime.start("Second mission outcome")
        with served(fx) as base:
            out.append(section("DONE historical proof with active-scoped legality", curl(f"{base}/api/overview?inspectMissionId={old_mission_id}")))
    finally:
        fx.close()

    output_path = ROOT / ".omo" / "evidence" / "task-5-signoff-ui-flow-http.txt"
    output_path.write_text("\n".join(out), encoding="utf-8")
    print(json.dumps({"path": str(output_path), "bytes": output_path.stat().st_size}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
