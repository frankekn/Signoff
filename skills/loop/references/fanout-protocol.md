# Fan-out protocol (shared MoA core)

Push and Pull both dispatch independent advisors through one mixture-of-agents fan-out. This document is authoritative for both phases. Mode-specific sealed packets and output contracts live in `push-mode.md` and `pull-mode.md`.

## Real heterogeneity

Advisors and reviewers must be real, separately dispatched subagent contexts on different provider/model wherever possible.

Each participant's identity tuple — `(participant_id, provider, model, context_id)` — is constituted by the actual dispatch. Never invent provider diversity, context IDs, or participant counts.

The host agent orchestrates dispatch. It does not count as an advisor or reviewer. The aggregator (chair for Push, lead judge for Pull) is a separate counted context that synthesizes; it does not substitute for advisor/reviewer quorum.

If the host cannot create ≥2 independent contexts:

- **Push:** record `INSUFFICIENT_QUORUM` in the decision verdict; do not imitate extra voices.
- **Pull:** stop and tell the user; insufficient review quorum is not recoverable by personas in one context.

## Non-actor advisor framing

An advisor or reviewer is NOT the acting agent. It cannot run tools, edit files, or modify anything in the repository. It analyzes the sealed packet supplied for its phase and returns advice for the aggregator.

Respond directly. No preamble, no disclaimers about lacking access, no requests to be given more context beyond the sealed packet. If information is missing from the packet, say so in the analysis; do not fetch it.

## Trimmed sealed packet

Advisors receive only the sealed artifacts and hashes for their phase — never the host's full conversation, prior advisor outputs (round one), or builder transcript.

**Push:** `GOAL.txt`, `CHARTER.md`, `SPEC.json`, and their SHA-256 values. Every advisor gets the identical question surface.

**Pull:** locked `CONTRACT.json`, runtime-generated `EVIDENCE.json`, runtime-generated `PATCH.diff`, their hashes, active acceptance IDs, and read-only source context needed to evaluate the patch against the contract.

Do not give one participant extra context, a different question, or another participant's first-round answer (except Push cross-examination, which is anonymized and bounded).

## Capped output

Advisor and reviewer responses should stay concise (~600 tokens guidance). The aggregator needs the gist of each judgment — verdict, route, risks, falsifiers, findings — not essays.

Long prose hides disagreement and wastes dispatch budget. Prefer structured, falsifiable claims over narrative.

## Parallel dispatch

Dispatch all advisors or reviewers at once. Latency is the slowest participant, not the sum.

Do not serialize round-one collection unless the host truly lacks parallel subagent capacity; even then, record honest timing and availability notes for the aggregator.

## Failure tolerance

A failed or unavailable advisor/reviewer becomes a labelled note in the aggregator's input, not an abort.

Quorum rules still apply to participants that returned substantive complete responses. A timeout, empty reply, or transport error is not a counted advisor. Do not backfill with simulated voices.

## Aggregator sole authorship

Exactly one aggregator context writes the phase artifact:

- **Push:** chair fills `PUSH.json`.
- **Pull:** lead judge fills `JUDGMENT.json` (reviewers write only their own `review-*.json`).

Advisors and reviewers never write phase artifacts beyond their assigned review file. No voting, no averaging, no "blended consensus" prose.

Material conflicts resolve only through:

```text
experiment
existing_evidence
locked_spec
user_decision
```

Preserve unresolved dissent instead of laundering it into confidence. Votes, majority, confidence scores, consensus labels, model brand, and rhetorical strength are invalid arbitration bases.

## Honesty norm

The protocol exists to make quorum real instead of self-reported. Traction does not claim measured MoA efficacy from this repository's conformance suite; external benchmarks (e.g. HermesBench aggregator/reference combinations) are cited in product docs as external evidence only.
