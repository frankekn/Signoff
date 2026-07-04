# Traction Protocol

The **Traction Protocol** is the versioned repository-local contract between users, coding agents, reviewers, and Grip. The runtime creates concrete run artifacts from the templates embedded in `src/traction/templates.py`. The JSON Schemas in `schemas/` document the agent-authored surfaces, while Python validators add cross-file rules that JSON Schema alone cannot enforce, including:

- exact run and artifact hash matching;
- stable ID references across spec and contract;
- unique real participant/context identities;
- verdict-split Push conflicts with evidence-based closure;
- machine-detected material advisor disagreement;
- builder/reviewer/judge role separation;
- complete acceptance and finding accounting;
- evidence-based rather than vote-based arbitration;
- cumulative final-contract requirements.

Schemas are documentation and editor support. The `./traction` runtime is the authoritative validator.

A successful terminal decision writes a **Receipt** that binds the locked outcome, exact patch, executed evidence, review decision, and ledger hashes.

## Vocabulary

| Term | Meaning |
|---|---|
| Traction | Product and push-pull engine |
| Grip | Deterministic engine that enforces legal transitions |
| Run | One user outcome from start to terminal state |
| Push | Pre-lock deliberation artifact (`PUSH.json`) |
| Pull | Post-verification independent review and judgment |
| Slice | One bounded implementation iteration |
| Receipt | Replayable evidence package for an accepted slice or completed run |
