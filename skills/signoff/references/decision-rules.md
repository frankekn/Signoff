# Decision rules

- `DONE`: final cumulative contract covers all locked requirements/criteria, verification passes, independent Roast passes, and no `ACT_ON` remains.
- `ACCEPTED`: current non-final slice passes; return to the locked mission for another bounded slice.
- `REWORK`: evidence or review identifies a contract-bound defect. Record a stable root cause.
- `PIVOT`: evidence shows the locked route/spec must change. Pause implementation, archive the old revision, and run a fresh Push.
- `STOPPED`: further work is lower value, unsafe, or unjustified.
- `BLOCKED`: required evidence, environment, permission, or honest independent quorum is unavailable.

Votes, confidence, consensus, and model brand are never valid conflict-resolution bases.
