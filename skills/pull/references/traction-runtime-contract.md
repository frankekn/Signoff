# Traction runtime contract

During a Traction run, generated `review-*.json` and `JUDGMENT.json` are canonical. `./traction pull` rejects self-review, duplicate contexts, wrong patch/evidence hashes, skipped acceptance IDs, silent finding drops, unresolved UNKNOWN/FAIL, and vote-based arbitration.
