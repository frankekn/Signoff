# Traction

> **The traction layer for coding agents.** Give it one plain-English outcome. Traction pushes deliberation, locks the target, bounds each build, runs executable verification, pulls independent review, and advances one notch — with proof.

Traction is a local, open-source push-pull engine around the coding agent you already use. It is not another model, IDE, workflow language, or multi-agent chat room.

The product vocabulary is intentionally small:

- **Traction** is the product name; this repository is `traction`.
- **Grip** is the deterministic engine inside Traction; agents may propose and challenge, but Grip alone advances state.
- **Traction Protocol** is the versioned set of artifacts, hashes, role boundaries, and legal transitions.
- A **Receipt** is the replayable evidence package produced for an accepted slice or completed run.

```text
user outcome
  → falsifiable contract
  → Push deliberation
  → hash lock
  → one bounded slice
  → executable evidence
  → Pull review
  → SIGNED OFF / REWORK / STOPPED / PIVOT / BLOCKED
```

## Push-pull engine

Traction converges by design:

1. **Push** (pre-lock planning deliberation) → **lock** → **build** → **Pull** (review against the locked contract) → **advance one notch**. Pull may only pull toward the locked target — reviewer taste and new ideas are not acceptance failures — so the loop moves forward instead of oscillating.

2. **A real mixture-of-agents collective provides quality.** Push and Pull default to ≥2 genuinely heterogeneous advisors (different provider/model, dispatched in parallel by the host agent). Solo mode is degraded and must be honestly marked `INSUFFICIENT_QUORUM`. An aggregator alone synthesizes and writes artifacts (chair for Push, judge for Pull); no voting, no averaging; material conflicts resolve only by experiment, existing evidence, locked spec, or user decision. External evidence: NousResearch's HermesBench reports an opus-4.8 aggregator with a gpt-5.5 reference at 0.8202 vs 0.7607 for opus alone — their result, not Traction's.

3. **The ratchet locks in what the collective decides.** Hash-locked goal, charter, spec, and contract mean the standard agreed before implementation cannot be quietly rewritten after. Executable verification is the oracle Pull compares against.

## Try it in two commands

Requirements: **Git** and **Python 3.10+**.

```sh
./install.sh
./traction ui
```

Open `http://127.0.0.1:8765`, enter the outcome, and use the UI to control and observe the run.

A disposable working demo is included:

```sh
./scripts/demo.sh
```

The demo opens an isolated repository at an active implementation slice. Change `app.py`, then run verification from the UI.

### Install into another repository

```sh
/path/to/traction/install.sh /path/to/your/repository
cd /path/to/your/repository
./traction ui
```

Windows PowerShell:

```powershell
.\install.ps1 C:\path\to\your\repository
cd C:\path\to\your\repository
.\traction.ps1 ui
```

The released UI is prebuilt. End users do **not** need Node.js, npm, Docker, a hosted account, or a global package install.

## Paste this into any coding agent

```text
Install Traction from <GITHUB_REPOSITORY_URL> into this repository.
Use it to achieve this exact outcome: <OUTCOME IN NORMAL LANGUAGE>.
Read AGENTS.md, run ./traction status and ./traction next, and perform exactly the legal next action.
Never edit locked artifacts or generated receipts. Do not claim completion unless Traction returns DONE.
```

Traction installs identical skills for generic agents, Claude Code, and Gemini-compatible skill directories while keeping the runtime repository-local.

## The UI

The local UI is deliberately simple:

- start a run with one sentence;
- see the single legal next action;
- edit only artifacts that are legal in the current phase;
- run scope checks, verification, Pull review, pivot, and terminal completion;
- inspect the immutable goal, contracts, evidence, patch receipts, and hash-chained timeline.

The UI is a Vite + React application using TanStack Router and TanStack Query. It is compiled into static assets and served by the dependency-free Python runtime.

## Why this is more than orchestration

A prompt that says “do not drift” does not change who controls the specification, tests, review, and completion claim. Traction moves those powers into machine-enforced gates.

| Failure mode | Structural control |
|---|---|
| Goal is quietly rewritten | Exact user sentence is stored verbatim and hash-bound |
| Acceptance criteria move after implementation | Charter, spec, Push decision, and slice contract are locked |
| Agent grades its own work | Builder, reviewers, and judge require distinct identities and contexts |
| Advisors answer different questions | Push advisors return route, falsifiable criteria, risk, first move, and cut; material conflicts are verdict-split |
| Consensus replaces truth | Material conflict needs an experiment, existing evidence, locked spec, or user decision |
| “Tests passed” exists only in prose | Runtime executes command arrays and records exit codes and output hashes |
| Adjacent cleanup spreads | Allowed paths plus file and changed-line budgets are measured from a Git snapshot |
| Tests mutate the patch under review | Verification fails when the patch changes during a check |
| Reviewer invents a new backlog | Every finding is dispositioned; out-of-contract work remains out of scope |
| `UNKNOWN` becomes a polite pass | Unresolved uncertainty cannot be promoted to SIGNED OFF |
| Process never converges | Iteration and repeated-root-cause gates force an explicit pivot or stop |
| Receipts are rewritten later | Artifact hashes and the append-only ledger are revalidated |

The initial version focuses on the reliable control boundary. It does not yet attempt a universal hidden-oracle synthesizer or autonomous provider router.

## CLI

```sh
./traction ui
./traction doctor
./traction start "Add Google sign-in without changing email login"
./traction status
./traction next

./traction prepare-push
./traction lock
./traction prepare-slice
./traction slice
./traction check-scope
./traction verify
./traction prepare-pull
./traction pull
./traction finish accepted
./traction finish done
./traction finish rework --root-cause "missing negative-path evidence"
./traction pivot --reason "the tested route cannot satisfy the locked outcome"
./traction integrity
./traction benchmark
```

Run artifacts live in `.traction/runs/<run-id>/`. Product code remains in the normal repository; Traction stores control state and receipts separately.

## What “effective” means

Traction keeps two claims separate.

### Protocol conformance

The deterministic suite asks whether the runtime rejects goal tampering, scope creep, fake quorum, self-review, evidence-free arbitration, mutated verification patches, and false completion.

```sh
python3 scripts/test.py
```

### Real-agent efficacy

A separate harness compares:

```text
coding agent alone
vs prompt-only loop
vs full Traction
```

under equal models, permissions, time, and cost, with hidden checks executed after the agent exits. The primary trust metric is **false completion rate**: patches Traction accepts that later fail held-out evidence.

The alpha does not claim improved real-agent coding success until controlled held-out experiments establish it. See [`docs/benchmarks.md`](docs/benchmarks.md).

## Development

End users do not need Node. Contributors changing the UI use Node 22.12+:

```sh
npm ci
npm run typecheck
npm run build:web
python3 scripts/test.py
python3 scripts/check_repo.py
```

Runtime code stays Python-standard-library-only. The prebuilt UI in `src/traction/web_dist/` must match `apps/web/dist/` after a production build.

## Repository layout

```text
apps/web/                 Vite + React + TanStack source
src/traction/             dependency-free runtime, local API, packaged UI
skills/                   traction and loop agent skills
protocol/schemas/         documented JSON artifact surfaces
tests/                    adversarial conformance and API tests
bench/                    controlled real-agent efficacy harness
scripts/                  install, demo, checks, and release tooling
```

## Security boundary

Traction executes verification commands declared inside the repository. Treat them as code. Use an OS or container sandbox for untrusted repositories and do not expose the local UI beyond localhost without an external security layer.

A local process with arbitrary filesystem access can forge identities or modify the runtime. The local alpha is tamper-evident, not a secure enclave. See [`SECURITY.md`](SECURITY.md) and [`docs/threat-model.md`](docs/threat-model.md).

Apache-2.0 licensed. Contributions and independent benchmark reproductions are welcome.
