# Signoff runtime contract

During a Signoff mission, generated `review-*.json` and `JUDGMENT.json` are canonical. `./signoff roast` rejects self-review, duplicate contexts, wrong patch/evidence hashes, skipped acceptance IDs, silent finding drops, unresolved UNKNOWN/FAIL, and vote-based arbitration.
