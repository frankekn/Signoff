# Mission Charter

- Mission: `mission-20260625-053118-c09decd4`
- Exact user outcome (immutable):

> Make contributor UI first-run install reproducible from the public npm lockfile and ensure Signoff patch receipts exclude control artifacts

## User-visible success

A contributor can clone the repository, run `npm ci`, then run the UI typecheck and production build from the public npm lockfile. Generated dependency/build outputs stay out of git status, and Signoff patch receipts contain only authorized product changes, not `.signoff/` control artifacts.

## Hard constraints

Keep the Python runtime dependency-free for end users. Preserve the one-path installation experience. Do not change UI behavior or Signoff protocol semantics except to make existing receipt filtering match existing scope filtering.

## Non-goals

Do not redesign the UI, add a package manager, add services, introduce Python runtime dependencies, or perform broad cleanup.

## Stop / pivot conditions

Stop if npm reproducibility is blocked by the local environment rather than repository metadata. Pivot if excluding `.signoff/` from patch receipts requires protocol-model changes rather than consistent control-path filtering.

## Evidence standard

`npm ci`, `npm run typecheck`, `npm run build:web`, `python3 scripts/test.py`, `python3 scripts/check_repo.py`, and generated-output git status checks must pass. A conformance test must prove sealed `PATCH.diff` excludes `.signoff/` control artifacts.
