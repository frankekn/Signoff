# Signoff

> **The signoff layer for coding agents.** Give it one plain-English outcome. Signoff keeps the target fixed, bounds each change, runs the evidence, and refuses signoff when proof is missing.

Signoff is a local, open-source control plane around the coding agent you already use. It is not another model, IDE, workflow language, or multi-agent chat room.

The product vocabulary is intentionally small:

- **Signoff** is the company/product name; this repository is `signoff`.
- **Court** is the deterministic decision engine inside Signoff; agents may propose and challenge, but Court alone advances state.
- **Signoff Protocol** is the versioned set of artifacts, hashes, role boundaries, and legal transitions.
- A **Receipt** is the replayable evidence package produced for an accepted slice or completed mission.

```text
user outcome
  → falsifiable contract
  → independent challenge
  → hash lock
  → one bounded patch
  → executable evidence
  → independent review
  → SIGNED OFF / REWORK / STOPPED / PIVOT / BLOCKED
```

## Try it in two commands

Requirements: **Git** and **Python 3.10+**.

```sh
./install.sh
./signoff ui
```

Open `http://127.0.0.1:8765`, enter the outcome, and use the UI to control and observe the mission.

A disposable working demo is included:

```sh
./scripts/demo.sh
```

The demo opens an isolated repository at an active implementation slice. Change `app.py`, then run verification from the UI.

### Install into another repository

```sh
/path/to/signoff/install.sh /path/to/your/repository
cd /path/to/your/repository
./signoff ui
```

Windows PowerShell:

```powershell
.\install.ps1 C:\path\to\your\repository
cd C:\path\to\your\repository
.\signoff.ps1 ui
```

The released UI is prebuilt. End users do **not** need Node.js, npm, Docker, a hosted account, or a global package install.

## Paste this into any coding agent

```text
Install Signoff from <GITHUB_REPOSITORY_URL> into this repository.
Use it to achieve this exact outcome: <OUTCOME IN NORMAL LANGUAGE>.
Read AGENTS.md, run ./signoff status and ./signoff next, and perform exactly the legal next action.
Never edit locked artifacts or generated receipts. Do not claim completion unless Signoff returns DONE.
```

Signoff installs identical skills for generic agents, Claude Code, and Gemini-compatible skill directories while keeping the runtime repository-local.

## The UI

The local UI is deliberately simple:

- start a mission with one sentence;
- see the single legal next action;
- edit only artifacts that are legal in the current phase;
- run scope checks, verification, review, pivot, and signoff;
- inspect the immutable goal, contracts, evidence, patch receipts, and hash-chained timeline.

The UI is a Vite + React application using TanStack Router and TanStack Query. It is compiled into static assets and served by the dependency-free Python runtime.

## Why this is more than orchestration

A prompt that says “do not drift” does not change who controls the specification, tests, review, and completion claim. Signoff moves those powers into machine-enforced gates.

| Failure mode | Structural control |
|---|---|
| Goal is quietly rewritten | Exact user sentence is stored verbatim and hash-bound |
| Acceptance criteria move after implementation | Charter, spec, Council decision, and slice contract are locked |
| Agent grades its own work | Builder, reviewers, and judge require distinct identities and contexts |
| Agents discuss different questions | Council advisors answer the same canonical claim registry |
| Consensus replaces truth | Material conflict needs an experiment, existing evidence, locked spec, or user decision |
| “Tests passed” exists only in prose | Runtime executes command arrays and records exit codes and output hashes |
| Adjacent cleanup spreads | Allowed paths plus file and changed-line budgets are measured from a Git snapshot |
| Tests mutate the patch under review | Verification fails when the patch changes during a check |
| Reviewer invents a new backlog | Every finding is dispositioned; out-of-contract work remains out of scope |
| `UNKNOWN` becomes a polite pass | Unresolved uncertainty cannot be promoted to signoff |
| Process never converges | Iteration and repeated-root-cause gates force an explicit pivot or stop |
| Receipts are rewritten later | Artifact hashes and the append-only ledger are revalidated |

The initial version focuses on the reliable control boundary. It does not yet attempt a universal hidden-oracle synthesizer or autonomous provider router.

## CLI

```sh
./signoff ui
./signoff doctor
./signoff start "Add Google sign-in without changing email login"
./signoff status
./signoff next

./signoff prepare-council
./signoff lock
./signoff prepare-slice
./signoff slice
./signoff check-scope
./signoff verify
./signoff prepare-roast
./signoff roast
./signoff finish accepted
./signoff finish done
./signoff finish rework --root-cause "missing negative-path evidence"
./signoff pivot --reason "the tested route cannot satisfy the locked outcome"
./signoff integrity
./signoff benchmark
```

Mission artifacts live in `.signoff/missions/<mission-id>/`. Product code remains in the normal repository; Signoff stores control state and receipts separately.

## What “effective” means

Signoff keeps two claims separate.

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
vs full Signoff
```

under equal models, permissions, time, and cost, with hidden checks executed after the agent exits. The primary trust metric is **false signoff rate**: patches Signoff accepts that later fail held-out evidence.

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

Runtime code stays Python-standard-library-only. The prebuilt UI in `src/signoff/web_dist/` must match `apps/web/dist/` after a production build.

## Repository layout

```text
apps/web/                 Vite + React + TanStack source
src/signoff/              dependency-free runtime, local API, packaged UI
skills/                   Signoff, Council, and Roast agent skills
protocol/schemas/         documented JSON artifact surfaces
tests/                    adversarial conformance and API tests
bench/                    controlled real-agent efficacy harness
scripts/                  install, demo, checks, and release tooling
```

## Security boundary

Signoff executes verification commands declared inside the repository. Treat them as code. Use an OS or container sandbox for untrusted repositories and do not expose the local UI beyond localhost without an external security layer.

A local process with arbitrary filesystem access can forge identities or modify the runtime. The local alpha is tamper-evident, not a secure enclave. See [`SECURITY.md`](SECURITY.md) and [`docs/threat-model.md`](docs/threat-model.md).

Apache-2.0 licensed. Contributions and independent benchmark reproductions are welcome.
