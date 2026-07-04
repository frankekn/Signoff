---
name: council
description: "Use before costly implementation to obtain independent, falsifiable PROCEED / STOP / PIVOT advice on the same decision surface. In Signoff mode, fill the generated COUNCIL.json and let ./signoff lock validate quorum, hashes, verdict-split conflicts, and conflict closure."
---

# Council — independent deliberation that can stop or pivot

Council is not a vote and not a multi-agent brainstorming chat. Its purpose is to create independent error signals before implementation and convert material disagreement into a discriminating observation.

## Signoff runtime mode

When `./signoff next` reports `COUNCIL`, use the generated `COUNCIL.json` as the output contract. Read the exact same sealed packet for every advisor:

- `GOAL.txt`;
- `CHARTER.md`;
- `SPEC.json`;
- their current SHA-256 values.

Never give one advisor extra context, a different question, or another advisor's first-round answer.

## Round one — blind and symmetric

Use at least two real fresh contexts. Each advisor must provide:

- a real identity tuple: participant ID, provider, model, context ID;
- `PROCEED`, `STOP`, or `PIVOT`;
- the smallest viable route this advisor recommends;
- falsifiable criteria — observable outcomes that would prove the route right or wrong;
- the strongest reason this route fails;
- one executable first move;
- what to cut from scope.

If the host cannot create independent contexts, record `INSUFFICIENT_QUORUM`. Never simulate additional advisors in one context or invent provider diversity.

## Conditional cross-examination

Only when advisors return different verdicts (`verdict-split`) receive a second round. Strip provider/model identity and label positions neutrally. Ask each side:

1. What precise claim from the opposing position is wrong?
2. What evidence supports that answer?
3. What cheapest observation would distinguish the two positions?
4. What result would make this advisor change its recommendation?

Do not open an unlimited conversation. One bounded cross-examination is enough to define the discriminating experiment.

## Chair synthesis

The chair frames and synthesizes but does not count as an advisor. The decision is one of:

- `PROCEED` — the smallest useful route is justified and provable;
- `STOP` — implementation is lower value than stopping;
- `PIVOT` — the goal or route must change before implementation;
- `INSUFFICIENT_QUORUM` — independent advice could not be obtained honestly.

Every material conflict must be closed with one of:

```text
experiment
existing_evidence
locked_spec
user_decision
```

Votes, majority, confidence, consensus, model brand, or rhetorical strength are invalid arbitration bases. Preserve unresolved dissent instead of laundering it into confidence.

After filling `COUNCIL.json`, run:

```sh
./signoff lock
```

The runtime—not the chair's prose—decides whether the artifact is valid.

General-purpose prompt references remain in `references/`, but Signoff's generated JSON and hashes take precedence during a mission.
