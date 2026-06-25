#!/usr/bin/env python3
"""Controlled baseline vs prompt-loop vs Signoff runner.

The harness deliberately executes hidden checks only after the agent exits. For real
secrecy, keep the manifest and evaluator outside the agent-writable filesystem and run
inside an OS/container boundary.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], *, cwd: Path, timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        proc = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        return {"status": "finished", "exit_code": proc.returncode, "duration_seconds": round(time.monotonic()-started,3), "stdout": proc.stdout, "stderr": proc.stderr}
    except subprocess.TimeoutExpired as exc:
        return {"status": "timeout", "exit_code": None, "duration_seconds": round(time.monotonic()-started,3), "stdout": exc.stdout or "", "stderr": exc.stderr or ""}
    except OSError as exc:
        return {"status": "error", "exit_code": None, "duration_seconds": round(time.monotonic()-started,3), "stdout": "", "stderr": str(exc)}


def git_output(project: Path, args: list[str]) -> str:
    proc = subprocess.run(["git", "-C", str(project), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return proc.stdout if proc.returncode == 0 else ""


def changed_metrics(project: Path) -> dict[str, Any]:
    files = sorted({x for x in (git_output(project,["diff","--name-only","HEAD","--","."]) + git_output(project,["ls-files","--others","--exclude-standard"])).splitlines() if x and not x.startswith(".signoff/")})
    added = deleted = 0
    for line in git_output(project,["diff","--numstat","HEAD","--","."]).splitlines():
        parts=line.split("\t")
        if len(parts)>=3:
            if parts[0].isdigit(): added += int(parts[0])
            if parts[1].isdigit(): deleted += int(parts[1])
    return {"changed_files":files,"changed_file_count":len(files),"changed_lines":added+deleted,"added_lines":added,"deleted_lines":deleted}


def render_prompt(mode: str, goal: str, signoff_url: str) -> str:
    if mode == "baseline":
        return goal
    if mode == "prompt-loop":
        return f"""Achieve this exact outcome: {goal}

Before editing, write a falsifiable specification. Work in small bounded slices. Run real tests, inspect the full diff, obtain independent critical review when possible, repair material findings, avoid unrelated cleanup, and stop or pivot rather than changing the goal. Do not claim completion without evidence.
"""
    if mode == "signoff":
        return f"""Install Signoff from {signoff_url} into this repository if it is not already installed.
Then use Signoff to achieve this exact outcome: {goal}
Follow ./signoff next until DONE, STOPPED, PIVOT, or BLOCKED. Do not bypass a failing gate.
"""
    raise ValueError(mode)


def expand_argv(template: list[str], mapping: dict[str,str]) -> list[str]:
    return [part.format(**mapping) for part in template]


def wilson(successes: int, total: int, z: float=1.96) -> tuple[float,float]:
    if total == 0: return (0.0,0.0)
    p=successes/total; d=1+z*z/total
    center=(p+z*z/(2*total))/d
    margin=z*math.sqrt((p*(1-p)+z*z/(4*total))/total)/d
    return (max(0.0,center-margin),min(1.0,center+margin))


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",required=True)
    ap.add_argument("--agent-argv-json",required=True,help='JSON argv array; placeholders: {project} {prompt} {prompt_file} {mode} {case_id} {python}')
    ap.add_argument("--modes",default="baseline,prompt-loop,signoff")
    ap.add_argument("--repetitions",type=int,default=1)
    ap.add_argument("--timeout-seconds",type=int,default=1800)
    ap.add_argument("--output",required=True)
    ap.add_argument("--signoff-source",default=str(ROOT))
    args=ap.parse_args()
    manifest_path=Path(args.manifest).resolve(); manifest=json.loads(manifest_path.read_text())
    argv_template=json.loads(args.agent_argv_json)
    if not isinstance(argv_template,list) or not all(isinstance(x,str) for x in argv_template): raise SystemExit("--agent-argv-json must be a JSON string array")
    modes=[x.strip() for x in args.modes.split(',') if x.strip()]
    results=[]
    for case in manifest["cases"]:
        fixture=(manifest_path.parent/case["fixture"]).resolve()
        for mode in modes:
            for repetition in range(1,args.repetitions+1):
                with tempfile.TemporaryDirectory(prefix=f"signoff-efficacy-{case['id']}-{mode}-") as tmp:
                    project=Path(tmp)/"project"; shutil.copytree(fixture,project)
                    if not (project/".git").exists():
                        subprocess.run(["git","init","-q",str(project)],check=True)
                        subprocess.run(["git","-C",str(project),"config","user.email","benchmark@example.invalid"],check=True)
                        subprocess.run(["git","-C",str(project),"config","user.name","Signoff Benchmark"],check=True)
                        subprocess.run(["git","-C",str(project),"add","."],check=True)
                        subprocess.run(["git","-C",str(project),"commit","-qm","benchmark baseline"],check=True)
                    prompt=render_prompt(mode,case["goal"],args.signoff_source)
                    prompt_file=Path(tmp)/"PROMPT.txt"; prompt_file.write_text(prompt)
                    mapping={"project":str(project),"prompt":prompt,"prompt_file":str(prompt_file),"mode":mode,"case_id":case["id"],"python":sys.executable}
                    agent=run(expand_argv(argv_template,mapping),cwd=project,timeout=args.timeout_seconds)
                    hidden=[]
                    for check in case.get("hidden_checks",[]):
                        h=run(check["command"],cwd=project,timeout=check.get("timeout_seconds",120))
                        h.update({"id":check["id"],"weight":check.get("weight",1.0)})
                        hidden.append(h)
                    hidden_success=all(x["status"]=="finished" and x["exit_code"]==0 for x in hidden)
                    combined=(agent.get("stdout","")+"\n"+agent.get("stderr",""))
                    completion_re=case.get("completion_regex",r"(?i)\b(done|complete|completed|finished|success)\b")
                    claimed=bool(re.search(completion_re,combined)) or (agent["status"]=="finished" and agent["exit_code"]==0)
                    weighted_total=sum(float(x["weight"]) for x in hidden) or 1.0
                    weighted_pass=sum(float(x["weight"]) for x in hidden if x["status"]=="finished" and x["exit_code"]==0)
                    metrics=changed_metrics(project)
                    allowed=set(case.get("expected_paths",[])); unnecessary=[p for p in metrics["changed_files"] if allowed and p not in allowed and not p.startswith((".agents/",".claude/",".gemini/")) and p not in {"signoff","signoff.cmd","signoff.ps1","AGENTS.md","CLAUDE.md","GEMINI.md"}]
                    signoff_phase=None
                    state=project/".signoff"/"state.json"
                    if state.exists():
                        try:
                            rs=json.loads(state.read_text()); mid=rs.get("active_mission_id")
                            if mid: signoff_phase=json.loads((project/".signoff"/"missions"/mid/"STATE.json").read_text()).get("phase")
                        except Exception: signoff_phase="INVALID_STATE"
                    results.append({"case_id":case["id"],"mode":mode,"repetition":repetition,"agent":agent,"hidden_checks":hidden,"task_success":hidden_success,"claimed_completion":claimed,"false_completion":bool(claimed and not hidden_success),"spec_retention_score":weighted_pass/weighted_total,"signoff_terminal_outcome":signoff_phase,"unnecessary_changed_files":unnecessary,"slop_file_ratio":len(unnecessary)/max(1,metrics["changed_file_count"]),**metrics})
    summary={}
    for mode in modes:
        rows=[r for r in results if r["mode"]==mode]; n=len(rows); wins=sum(r["task_success"] for r in rows); false=sum(r["false_completion"] for r in rows)
        low,high=wilson(wins,n)
        summary[mode]={"runs":n,"successes":wins,"success_rate":wins/n if n else 0,"success_wilson_95":[low,high],"false_completions":false,"false_completion_rate":false/max(1,sum(r["claimed_completion"] for r in rows)),"mean_spec_retention":sum(r["spec_retention_score"] for r in rows)/n if n else 0,"mean_duration_seconds":sum(r["agent"]["duration_seconds"] for r in rows)/n if n else 0}
    output={"schema_version":1,"manifest":str(manifest_path),"modes":modes,"repetitions":args.repetitions,"summary":summary,"runs":results}
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(summary,indent=2))
    return 0

if __name__=="__main__": raise SystemExit(main())
