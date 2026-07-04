# Traction runtime contract

During a Traction run, generated artifacts are canonical. Preserve exact artifact hashes.

**Push phase:** `PUSH.json` is the output. `./traction lock` rejects fake quorum, duplicate contexts, unresolved verdict-split conflicts, and vote-based arbitration.

**Pull phase:** `review-*.json` and `JUDGMENT.json` are canonical. `./traction pull` rejects self-review, duplicate contexts, wrong patch/evidence hashes, skipped acceptance IDs, silent finding drops, unresolved UNKNOWN/FAIL, and vote-based arbitration.

See `push-mode.md` and `pull-mode.md` for phase-specific contracts.
