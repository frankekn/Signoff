# Artifact guide

The runtime creates one run directory under `.traction/runs/<run-id>/`.

Agent-authored inputs:

- `CHARTER.md` — user-visible success, hard constraints, non-goals, stop/pivot conditions, evidence standard;
- `SPEC.json` — stable requirements and falsifiable acceptance criteria;
- `PUSH.json` — independent advisor routes, falsifiable criteria, risks, route synthesis, and evidence-based synthesis of verdict splits and chair overrides;
- `iterations/<n>/CONTRACT.json` — one bounded implementation slice;
- `reviews/review-*.json` — read-only criterion decisions and findings;
- `JUDGMENT.json` — complete finding accounting and evidence-based conflict resolution.

Runtime-generated receipts must never be edited:

- `GOAL.txt`, `LOCK.json`, `GUARD.json`, `EVIDENCE.json`, `PATCH.diff`, `REVIEW_GATE.json`, `LEDGER.jsonl`, and every `STATE.json`.

Use `./traction next` for the current path and `./traction integrity` to revalidate locks and receipts.
