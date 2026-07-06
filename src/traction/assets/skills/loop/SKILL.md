---
name: loop
description: "Use when ./traction next reports PUSH (pre-lock deliberation) or REVIEWING (sealed-patch review). Runs the shared MoA fan-out protocol: independent heterogeneous advisors, one aggregator, capped output, parallel dispatch."
---

# Loop — Push and Pull via shared MoA fan-out

Traction advances one notch per cycle:

```text
Push → lock → build → verify → Pull → finish or rework
```

Push is pre-lock planning deliberation that fills `PUSH.json` and gates on `./traction lock`. Pull is post-verification review of one sealed patch that fills `reviews/review-*.json` and `JUDGMENT.json` and gates on `./traction pull`. This skill covers both phases. `./traction next` tells you which mode applies.

Neither phase is a vote, brainstorm chat, or taste tribunal. Both exist to create independent error signals before or after implementation and to close material disagreement with evidence—not confidence, majority, or model brand.

## Shared fan-out protocol

Read `references/fanout-protocol.md` before dispatching any advisor or reviewer. Both phases share one MoA core:

- real heterogeneous contexts (different provider/model where possible);
- trimmed sealed packets and capped advisor output;
- parallel dispatch;
- failure-tolerant partial quorum with honest labelling;
- exactly one aggregator that alone writes the phase artifact.

If the host cannot establish ≥2 independent contexts:

- **Push:** record `INSUFFICIENT_QUORUM` in `PUSH.json` and run `./traction lock`.
- **Pull:** stop and tell the user; do not run `./traction pull` with simulated reviewers.

Never simulate additional advisors or reviewers in one context. Identity tuples are constituted by dispatch, not self-reported strings.

## Push mode

When `./traction next` reports `PUSH`, follow `references/push-mode.md`.

Give every advisor the same sealed packet: `GOAL.txt`, `CHARTER.md`, `SPEC.json`, and their SHA-256 hashes. Fill the generated `PUSH.json`. Material verdict splits require one bounded cross-examination round. Then run:

```sh
./traction lock
```

The runtime—not the chair's prose—decides validity.

## Pull mode

When `./traction next` reports `REVIEWING`, follow `references/pull-mode.md`.

Give every reviewer the same locked `CONTRACT.json`, `EVIDENCE.json`, `PATCH.diff`, hashes, and read-only source context. Fill every generated `reviews/review-*.json` and `JUDGMENT.json`. Then run:

```sh
./traction pull
```

Do not edit files merely to make the gate green; repair underlying evidence or implementation.

## Reference map

| File | Purpose |
|---|---|
| `references/fanout-protocol.md` | Shared MoA core (authoritative) |
| `references/push-mode.md` | Push sealed packet, advisor contract, chair synthesis |
| `references/pull-mode.md` | Pull inputs, reviewer duties, lead judgment |
| `references/deliberation-prompt.md` | Push advisor template |
| `references/cross-examination-prompt.md` | Push verdict-split round 2 |
| `references/reviewer-prompt.md` | Pull reviewer template |
| `references/rubric.md` | Review lenses |
| `references/lead-judgment.md` | Lead judge duties |
| `references/cli-reviewers.md` | Reviewer transport adapters |
| `references/code-quality-review.md` | Code-quality lens |
| `references/traction-runtime-contract.md` | Runtime gate summary |

Generated JSON and hashes override reference prose during a Traction run.
