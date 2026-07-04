# Evidence-based debate protocol

Multi-agent debate is useful only when it creates independent error signals and converts disagreement into a discriminating observation. More agents, more turns, or stronger rhetoric do not automatically improve truth.

Traction uses two bounded debate surfaces: **Push** before implementation and **Pull** after verification.

## Shared principles

1. **Blind first round.** Participants do not see peer answers or identities before forming an initial position.
2. **Symmetric brief and sealed packet.** Every participant receives the same goal, constraints, evidence, and artifact hashes.
3. **Explicit null hypothesis.** “Do not build” or “the patch is not proven” must remain legitimate outcomes.
4. **Falsifiable claims.** Every material position states what observation would change it.
5. **One conditional cross-examination.** Only material conflicts receive a second round; there is no open-ended chat.
6. **Identity stripping.** Cross-examination packets use position aliases to reduce status and vendor anchoring.
7. **Evidence-based closure.** Experiments, existing receipts, or the locked spec resolve conflict. Votes do not.
8. **Preserved dissent.** Unresolved dissent remains visible and lowers or blocks the proof claim.

## Push: should we build this?

### Round-one input

Each advisor receives:

- the user's exact goal;
- current system evidence;
- hard constraints and non-goals;
- draft spec and canonical hash;
- required null hypothesis;
- request for the smallest high-leverage plan.

### Round-one output

Each advisor returns:

- `PROCEED`, `STOP`, or `PIVOT`;
- `route` — the proposed path in plain language;
- `falsifiable_criteria` — observable checks that would falsify the route;
- `risk` — what could go wrong;
- `first_move` — the first executable step if proceeding;
- `cut` — what should be deferred or removed.

Advisors no longer answer a fixed four-topic claim registry. Material disagreement is detected from verdict splits and substantive field conflicts instead.

### Material conflict test

Cross-examination is required when any of these differ materially:

- verdict;
- whether the goal is feasible or valuable under constraints;
- a must-have acceptance criterion;
- the first irreversible move;
- a safety or migration assumption;
- evidence needed before implementation.

Stylistic differences and alternative wording are not material conflict.

### Push decision

The chair may synthesize but does not invent a majority rule. A `PROCEED` decision must name why the null hypothesis lost, what was cut, and what dissent remains. `STOP` and `PIVOT` are normal successful outputs. `INSUFFICIENT_QUORUM` is an honest degraded outcome when fewer than two heterogeneous advisors participated.

## Pull: does this exact patch satisfy this exact spec?

### Independent review input

Every reviewer receives the same immutable package:

- locked charter/spec and active contract;
- exact patch and SHA-256;
- acceptance receipts and scope report;
- relevant surrounding code;
- finding schema.

The builder receives none of the other reviewers' drafts.

### Acceptance position

For each acceptance ID, a reviewer returns:

```json
{
  "acceptance_id": "A-001",
  "stance": "PASS | FAIL | UNKNOWN",
  "claim": "what is believed",
  "evidence": "specific observation",
  "falsifier": "observation that would reverse this stance"
}
```

Reviewers also create bounded finding cards categorized as code defect, evidence gap, scope drift, spec gap, or slop.

`UNKNOWN` preserves uncertainty; it is never counted as positive proof. A reviewer can only return overall PASS when all of its active acceptance positions are PASS. The lead judge is a fresh context distinct from the builder and every reviewer, and may only return PASS when all acceptance positions resolve PASS through direct agreement or an evidence-based dispute.

## Conflict-to-experiment algorithm

For every PASS/FAIL pair:

1. Normalize both positions to one claim about one acceptance criterion.
2. Remove reviewer identity and confidence score.
3. Extract each stated falsifier.
4. List candidate observations that distinguish the positions.
5. Choose the cheapest observation with adequate discriminating power.
6. Run it through the evidence boundary where possible.
7. Let each reviewer DEFEND or REVISE exactly once after seeing the anonymized opposing claim and new evidence; every position alias must return an updated stance, reason, and falsifier.
8. Reject missing, duplicate, or invented aliases, then record `PASS`, `FAIL`, or `UNRESOLVED`, with evidence references.

Examples of discriminating observations:

- a targeted regression test;
- a direct source/AST query;
- replaying the original failure fixture;
- a property test over the disputed edge case;
- a migration dry run against a copied schema;
- a held-out evaluator for user-visible behavior.

## Why confidence and votes are excluded

Confidence is model-specific and poorly calibrated across tasks. Votes amplify correlated errors when reviewers share training, prompts, tools, or an incorrect assumption. Traction records identities for provenance but removes them from the argument packet and requires a basis tied to the claim.

## Anti-collusion and anti-groupthink controls

- fresh context declared for every reviewer;
- builder identity barred from review and lead judgment;
- identical patch hash enforced;
- raw first-round positions preserved before cross-examination;
- high/blocker topics raised independently by multiple reviewers require concrete disproof to dismiss;
- at most five `ACT_ON` root causes, preventing a consensus-generated backlog;
- spec gaps return to Push instead of becoming unreviewed implementation scope.

## Honest limitation

A generic file-based protocol cannot prove that a closed-source host truly created independent sessions. Host adapters should capture signed session IDs or process-level evidence when available. Until then, independence metadata is an auditable assertion, not cryptographic attestation.
