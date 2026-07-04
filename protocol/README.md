# Signoff Protocol

The **Signoff Protocol** is the versioned repository-local contract between users, coding agents, reviewers, and Court. The runtime creates concrete run artifacts from the templates embedded in `src/signoff/templates.py`. The JSON Schemas in `schemas/` document the agent-authored surfaces, while Python validators add cross-file rules that JSON Schema alone cannot enforce, including:

- exact run and artifact hash matching;
- stable ID references across spec and contract;
- unique real participant/context identities;
- complete canonical Push topic coverage;
- machine-detected SUPPORT/OPPOSE conflicts;
- builder/reviewer/judge role separation;
- complete acceptance and finding accounting;
- evidence-based rather than vote-based arbitration;
- cumulative final-contract requirements.

Schemas are documentation and editor support. The `./signoff` runtime is the authoritative validator.

A successful terminal decision writes a **Receipt** that binds the locked outcome, exact patch, executed evidence, review decision, and ledger hashes.
