# Push mode — pre-lock deliberation

Apply when `./traction next` reports `PUSH`. Follow `fanout-protocol.md` for dispatch mechanics.

## Sealed packet

Every advisor receives exactly:

- `GOAL.txt`;
- `CHARTER.md`;
- `SPEC.json`;
- their current SHA-256 values.

Never give one advisor extra context, a different question, or another advisor's first-round answer.

## Round one — blind and symmetric

Use at least two real fresh contexts per `fanout-protocol.md`. Each advisor must provide:

- a real identity tuple: participant ID, provider, model, context ID;
- `PROCEED`, `STOP`, or `PIVOT`;
- the smallest viable route this advisor recommends;
- falsifiable criteria — observable outcomes that would prove the route right or wrong;
- the strongest reason this route fails;
- one executable first move;
- what to cut from scope.

If the host cannot create independent contexts, record `INSUFFICIENT_QUORUM`. Never simulate additional advisors in one context.

Prompt template: `deliberation-prompt.md`.

## Material conflict cross-examination

When advisors return different verdicts (`verdict-split`) or materially different routes (`route-divergence`), run a second round. One bounded round only — never open unlimited conversation.

Strip provider/model identity. Label opposing positions neutrally. Ask each side:

1. What precise claim from the opposing position is wrong?
2. What evidence supports that answer?
3. What cheapest observation would distinguish the two positions?
4. What result would make this advisor change its recommendation?

Prompt template: `cross-examination-prompt.md`.

## Chair synthesis

The chair frames and synthesizes but does not count as an advisor. The decision verdict is one of:

- `PROCEED` — the smallest useful route is justified and provable;
- `STOP` — implementation is lower value than stopping;
- `PIVOT` — the goal or route must change before implementation;
- `INSUFFICIENT_QUORUM` — independent advice could not be obtained honestly.

Every material conflict must be closed with one of: `experiment`, `existing_evidence`, `locked_spec`, `user_decision`.

If all advisors agree on a verdict and the chair chooses a different verdict, record an evidence-based `advisor-unanimous-<verdict>` resolution unless the chair chooses `STOP`. Stopping is always an honest terminal decision.

Votes, majority, confidence, consensus, model brand, or rhetorical strength are invalid arbitration bases. Preserve unresolved dissent instead of laundering it into confidence.

Fill the generated `PUSH.json`. The chair alone writes it. Advisors never write artifacts.

Then run:

```sh
./traction lock
```

The runtime—not the chair's prose—decides whether the artifact is valid.
