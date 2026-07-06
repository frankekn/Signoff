# Pull mode — sealed-patch review

Apply when `./traction next` reports `REVIEWING`. Follow `fanout-protocol.md` for dispatch mechanics.

## Inputs

Every reviewer receives the same:

- locked `CONTRACT.json` and its hash;
- runtime-generated `EVIDENCE.json` and its hash;
- runtime-generated `PATCH.diff` and its hash;
- active acceptance IDs;
- relevant source context, read-only.

Use the generated `reviews/review-*.json` files. Do not alter the patch, evidence, contract, or another reviewer's file.

Run `./traction prepare-pull` first if the runtime has not yet generated review templates.

## Independent reviews

Use at least two real fresh contexts distinct from the builder and from one another. Each reviewer must:

1. attest `read_only: true`;
2. answer every acceptance ID exactly once with `PASS`, `FAIL`, or `UNKNOWN`;
3. cite receipt/check IDs where evidence exists;
4. state a reason tied to the locked criterion;
5. emit structured findings with severity, claim, evidence, falsifier, and recommended disposition.

`UNKNOWN` is preserved uncertainty, not a weak pass. Reviewer taste, optional refactors, and new product ideas are not acceptance failures unless the locked spec requires them.

Prompt templates: `reviewer-prompt.md`, `rubric.md`, `code-quality-review.md`. Transport notes: `cli-reviewers.md`.

## Lead judgment

A third real context acts as lead judge. It cannot be the builder or a counted reviewer. It fills `JUDGMENT.json` and must:

- decide every acceptance ID;
- account for every finding exactly once;
- retain `ACT_ON`, `CONSIDER`, `NOTED`, `DISMISSED`, or `OUT_OF_SCOPE` explicitly;
- provide evidence when dismissing a critical/high finding;
- preserve unresolved uncertainty;
- avoid adding reviewer suggestions to the spec.

Details: `lead-judgment.md`.

## Conflict arbitration

A material PASS/FAIL or PASS/UNKNOWN conflict cannot be settled by majority, confidence, consensus, model authority, or provider brand. It requires a passed experiment, existing evidence receipt, locked-spec interpretation, or explicit user decision.

If a new experiment is needed, return to verification and obtain a fresh review of the new sealed patch.

## Runtime gate

After all files are complete, run:

```sh
./traction pull
```

The runtime validates identities, hashes, complete criterion coverage, finding accounting, and conflict resolution. Do not edit files merely to make the gate green; repair the underlying evidence or implementation.
