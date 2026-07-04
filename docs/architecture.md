# Architecture

Traction separates probabilistic reasoning from deterministic authority.

## Layers

### 1. Human product surface

The user provides one exact outcome. They do not configure a workflow graph, provider matrix, or reviewer rubric. `./traction next` keeps the visible path linear.

### 2. Local UI and API

`src/traction/web.py` serves a localhost JSON API and the prebuilt Vite application in `web_dist/`. The UI uses TanStack Query for polling/mutations and TanStack Router for navigation.

There is intentionally no separate database in the alpha. Files under `.traction/` are the single source of truth for both CLI and UI, which avoids synchronization bugs and keeps every run portable with the repository. The API only allows edits to artifacts that are legal in the current phase.

### 3. Agent skills

The traction and loop skills tell coding agents how to author the next artifact. Skills may reason, propose, and critique. They cannot advance state on their own.

### 4. Grip engine

**Grip** is the deterministic core mechanism. It does not generate plans or code; it validates artifacts, enforces role and evidence boundaries, and is the only component allowed to advance the run state. `src/traction/runtime.py` owns the legal transitions:

```text
IDLE → DRAFT → PUSH → LOCKED → SLICE_DRAFT → IMPLEMENTING
     → VERIFIED → REVIEWING → REVIEWED → LOCKED | DONE
```

Failure or convergence paths include `VERIFY_FAILED`, `PUSH_REVIEW`, `STOPPED`, `PIVOT`, and `BLOCKED`.

### 5. Artifact validators

`schemas.py` validates local structure and cross-artifact invariants. JSON Schemas in `protocol/schemas/` provide editor/documentation support; Python validation is authoritative because it can compare hashes, identities, IDs, and evidence receipts.

### 6. Git-backed scope

Each run and slice uses an unreachable synthetic Git commit as an exact baseline. It is built through a temporary index under `.git/traction/`, so the user's branch, worktree, and staging area are not changed.

Scope is computed from:

- changed files since the slice baseline;
- `allowed_paths`, `forbidden_paths`, and `exempt_paths`;
- production-file count;
- added plus deleted lines.

Mid-iteration commits cannot hide changes because comparison remains anchored to the recorded synthetic commit.

### 7. Evidence and audit

Verification executes command arrays with `shell=False`, captures exit status and bounded stdout/stderr, hashes full outputs, writes the exact patch, and checks that running commands did not mutate that patch.

Every transition appends to `LEDGER.jsonl`. Each record includes the previous hash and its own canonical record hash. The ledger is tamper-evident, not tamper-proof.

## Why local-first

Local artifacts are inspectable, portable across coding-agent hosts, compatible with normal Git workflows, and do not require a hosted control plane. A future hosted service may add isolated execution, team policy, encrypted evidence, and benchmark aggregation without changing the repository protocol.

## Trust boundary

The runtime assumes the local process can read and write the repository. It detects common tampering but cannot defend against an adversary with arbitrary process/filesystem control. Strong isolation belongs in an external evaluator or container runner.

## Product vocabulary

The user-facing product is **Traction**. The repository contract is the **Traction Protocol**. The deterministic authority described above is **Grip**. Completed evidence is emitted as a **Receipt**. These names are kept separate so the product reads as forward motion while the architecture still has a precise name for its adjudication mechanism.
