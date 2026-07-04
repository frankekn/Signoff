# Mission Charter

- Mission: `mission-20260625-051108-2c506d76`
- Exact user outcome (immutable):

> Make the contributor UI first-run install reproducible from the public npm lockfile without leaving generated dependency or build outputs untracked

## User-visible success

A contributor can clone the repository, run `npm ci`, then run the UI typecheck and production build from the public npm lockfile. The resulting dependency and build directories do not appear as untracked product changes.

## Hard constraints

Keep the Python runtime dependency-free for end users. Do not change product behavior, protocol gates, mission artifacts, or the packaged UI runtime except for generated assets if the UI build requires it.

## Non-goals

Do not redesign the UI, change Signoff state-machine semantics, add a package manager, or introduce new runtime services.

## Stop / pivot conditions

Stop if the npm install failure is caused by the local environment rather than repository metadata. Pivot if making `npm ci` reproducible requires changing package manager or dependency strategy.

## Evidence standard

`npm ci`, `npm run typecheck`, `npm run build:web`, `python3 scripts/test.py`, and `python3 scripts/check_repo.py` must pass. `git status --short` must not show generated dependency or build outputs.
