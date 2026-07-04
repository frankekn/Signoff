---
name: pull
description: "Use after executable verification for independent read-only review of one sealed patch against one locked contract. In Signoff mode, fill review-*.json and JUDGMENT.json; ./signoff pull enforces role separation, complete criterion coverage, finding accounting, and evidence-based conflict closure."
disable-model-invocation: true
---

# Pull — adversarial review of one sealed patch

Pull does not redesign the product and does not auto-apply suggestions. It asks whether one exact patch satisfies one exact contract using one exact evidence bundle.

## Inputs in Signoff mode

When `./signoff next` reports `REVIEWING`, every reviewer receives the same:

- locked `CONTRACT.json` and its hash;
- runtime-generated `EVIDENCE.json` and its hash;
- runtime-generated `PATCH.diff` and its hash;
- active acceptance IDs;
- relevant source context, read-only.

Use the generated `reviews/review-*.json` files. Do not alter the patch, evidence, contract, or another reviewer's file.

## Independent reviews

Use at least two real fresh contexts distinct from the builder and from one another. Each reviewer must:

1. attest `read_only: true`;
2. answer every acceptance ID exactly once with `PASS`, `FAIL`, or `UNKNOWN`;
3. cite receipt/check IDs where evidence exists;
4. state a reason tied to the locked criterion;
5. emit structured findings with severity, claim, evidence, falsifier, and recommended disposition.

`UNKNOWN` is a preserved uncertainty, not a weak pass. Reviewer taste, optional refactors, and new product ideas are not acceptance failures unless the locked spec requires them.

## Lead judgment

A third real context acts as lead judge and cannot be the builder or a counted reviewer. It fills `JUDGMENT.json` and must:

- decide every acceptance ID;
- account for every finding exactly once;
- retain `ACT_ON`, `CONSIDER`, `NOTED`, `DISMISSED`, or `OUT_OF_SCOPE` explicitly;
- provide evidence when dismissing a critical/high finding;
- preserve unresolved uncertainty;
- avoid adding reviewer suggestions to the spec.

A material PASS/FAIL or PASS/UNKNOWN conflict cannot be settled by majority, confidence, consensus, model authority, or provider brand. It requires a passed experiment, existing evidence receipt, locked-spec interpretation, or explicit user decision. If a new experiment is needed, return to verification and obtain a fresh review of the new sealed patch.

## Runtime gate

After all files are complete, run:

```sh
./signoff pull
```

The runtime validates identities, hashes, complete criterion coverage, finding accounting, and conflict resolution. Do not edit files merely to make the gate green; repair the underlying evidence or implementation.

Detailed rubrics remain in `references/`. The generated artifact contract is authoritative during Signoff missions.
