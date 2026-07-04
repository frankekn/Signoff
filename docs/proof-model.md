# Proof model

Traction distinguishes evidence from confidence.

## Proof objects

A completion claim is supported by independently checkable objects:

- an exact user-goal hash;
- locked charter/spec/Push hashes;
- one bounded contract and builder identity;
- a Git baseline and exact patch;
- executed command receipts with exit codes and output hashes;
- scope and budget calculations;
- sealed reviews and judgment;
- a hash-chained transition ledger.

No individual object is sufficient. The gate composes them.

## Proof levels

### Tested

All active verification commands passed, locks remained valid, scope stayed inside the contract, and verification did not mutate the patch.

### Peer-reviewed

At least two fresh read-only contexts reviewed the same patch, contract, and evidence. The builder and lead judge are excluded from reviewer quorum.

### Diverse-reviewed

Peer-reviewed, with at least two distinct provider/model tuples. Diversity is a useful independent-error signal, not a substitute for evidence.

### External

A held-out evaluator, production metric, or explicit human acceptance receipt passed outside the builder/reviewer filesystem boundary. The local alpha runtime does not manufacture this label.

## Unknown and dissent

`UNKNOWN` is a first-class state. It lowers the proof claim or blocks completion. Dissent is preserved until a discriminating experiment, existing receipt, locked-spec interpretation, or explicit user decision resolves it.

## Claim boundary

Passing the protocol conformance suite proves only that the controls reject known invalid states. It does not prove that models write better code. Real-agent efficacy requires held-out tasks, controlled budgets, hidden evaluation, and public failure accounting.
