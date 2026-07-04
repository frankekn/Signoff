# Mission Charter

- Mission: `mission-20260625-051108-2c506d76`
- Exact user outcome (immutable):

> Make the contributor UI first-run install reproducible from the public npm lockfile without leaving generated dependency or build outputs untracked

## User-visible success

A contributor can clone the repository, run `npm ci`, then run the UI typecheck and production build from the public npm lockfile. Generated dependency/build outputs stay out of git status, and Signoff receipts show only the authorized product patch rather than `.signoff/` control artifacts.

## Hard constraints

Keep the Python runtime dependency-free for end users. Do not change UI behavior, Signoff protocol semantics, or the one-path installation experience except where needed to make receipts accurately exclude Signoff control state.

## Non-goals

Do not redesign the UI, add a package manager, add runtime dependencies, introduce services, or make broad cleanup changes.

## Stop / pivot conditions

Stop if npm reproducibility is blocked by the local environment rather than repository metadata. Pivot if receipt correctness requires changing the protocol model rather than filtering existing control paths consistently.

## Evidence standard

`npm ci`, `npm run typecheck`, `npm run build:web`, `python3 scripts/test.py`, `python3 scripts/check_repo.py`, and generated-output git status checks must pass. A conformance test must prove sealed `PATCH.diff` excludes `.signoff/` control artifacts.
