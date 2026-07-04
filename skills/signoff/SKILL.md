---
name: signoff
description: "Use for engineering work that must autonomously write a specification, obtain independent Council pressure, implement one bounded slice, prove it with executable receipts, obtain independent Roast review, and continue without goal drift or AI slop. The ./signoff state machine is authoritative."
disable-model-invocation: true
---

# Signoff

Signoff is the reliability control plane around the coding agent. The user supplies one outcome in ordinary language. The agent follows the repository-local state machine until it emits `DONE`, `STOPPED`, `PIVOT`, or `BLOCKED`.

The model transcript is never authoritative. Run:

```sh
./signoff status
./signoff next
```

Then perform exactly the one legal action returned by `./signoff next`.

## Non-negotiable rules

1. Preserve the user's exact outcome in `GOAL.txt`; never paraphrase it in `./signoff start`.
2. Do not edit any artifact after its hash is locked. A changed goal, charter, or spec requires the pivot gate and a fresh Council.
3. Work on one contract only. Do not touch files outside `allowed_paths`, exceed file/line budgets, or introduce adjacent cleanup.
4. A builder cannot count as a reviewer or lead judge. Context IDs must represent real fresh contexts; never manufacture quorum.
5. Claims such as “tests pass” are invalid until `./signoff verify` executes the commands and seals `EVIDENCE.json` plus `PATCH.diff`.
6. Reviewers are read-only. Their suggestions do not become requirements; out-of-spec work stays `OUT_OF_SCOPE`.
7. `UNKNOWN` is not `PASS`. A disagreement can close only through a passed experiment, existing receipt, locked spec, or explicit user decision—not votes, confidence, consensus, or model brand.
8. Do not continue after a terminal state.

## The one path

### DRAFT

Complete the generated `CHARTER.md` and `SPEC.json`.

The charter states user-visible success, hard constraints, non-goals, stop/pivot conditions, and evidence standard. The spec uses stable requirement and acceptance IDs. Every must requirement maps to a falsifiable acceptance criterion.

Then run:

```sh
./signoff prepare-council
```

### COUNCIL

Use the sibling `council` skill. Give every advisor the exact same goal, charter, spec, and hashes.

Advisors answer independently before seeing peers. Fill the generated `COUNCIL.json`. Material verdict splits require an evidence-based resolution. If independent contexts are unavailable, return `INSUFFICIENT_QUORUM`; do not imitate extra voices.

Then run:

```sh
./signoff lock
```

### LOCKED / SLICE_DRAFT

Create one bounded slice:

```sh
./signoff prepare-slice
```

Complete `CONTRACT.json` with one real builder identity, requirement/acceptance IDs from the locked spec, allowed and forbidden path globs, production-file and changed-line budgets, and executable verification commands. Keep the slice as small as possible while remaining coherent.

Activate it:

```sh
./signoff slice
```

### IMPLEMENTING

Make the smallest coherent change that satisfies the active contract. Do not change locked artifacts, generated receipts, or unrelated files. Then run:

```sh
./signoff verify
```

A failed command, scope breach, budget overflow, timeout, or verification-induced patch mutation is a real failure. Fix the cause and verify again; never edit the receipt.

### VERIFIED / REVIEWING

Create sealed review packets:

```sh
./signoff prepare-roast
```

Use the sibling `roast` skill in fresh read-only contexts. Every reviewer answers every active acceptance ID with `PASS`, `FAIL`, or `UNKNOWN` against the same contract, evidence, and patch hashes. A separate lead judge accounts for every finding and conflict.

Then run:

```sh
./signoff roast
```

### REVIEWED

Follow the deterministic result:

```sh
./signoff finish accepted
./signoff finish done
./signoff finish rework --root-cause "<stable root cause>"
```

`DONE` requires a final cumulative contract that covers every locked requirement and acceptance criterion. Repeated root causes or two review cycles without accepted progress force `COUNCIL_REVIEW`; implementation must pause until a pivot or stop decision.

## User-facing progress

Do not dump internal JSON unless asked. Report only:

- the active bounded slice;
- executable evidence and whether scope stayed locked;
- unresolved disagreement or blocker;
- the final terminal result and residual risk.

A truthful stop is better than a plausible-looking completion claim.
