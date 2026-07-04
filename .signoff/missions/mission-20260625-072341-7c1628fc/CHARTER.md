# Mission Charter

- Mission: `mission-20260625-072341-7c1628fc`
- Exact user outcome (immutable):

> UI should allow starting the next mission after a DONE mission

## User-visible success

A completed Signoff mission still shows its signed-off receipt, and the same page also lets the user enter a new outcome and start the next mission. After submit, the UI changes to the new mission in DRAFT with editable CHARTER.md and SPEC.json.

## Hard constraints

- Preserve terminal DONE meaning: no implementation may continue under the completed mission.
- Do not change runtime start rules, lock rules, Council, Verify, Roast, or receipt semantics.
- Preserve the existing local-only UI and zero runtime dependency posture.
- Keep the change limited to the contributor web UI and the generated shipped UI bundle.

## Non-goals

- Do not build a full browser-based agent runner.
- Do not add authentication, hosted state, background jobs, or new services.
- Do not redesign the UI or change phase/action semantics beyond exposing the existing start path after DONE.

## Stop / pivot conditions

- Stop if starting the next mission requires weakening the terminal DONE contract.
- Pivot if the runtime cannot safely start a new mission after DONE through the existing /api/missions endpoint.
- Stop if proof requires mutating a real completed mission instead of a disposable Git test project.

## Evidence standard

- TypeScript typecheck passes.
- The packaged UI build is regenerated.
- The Python conformance and web API suite passes.
- Repository structural check passes.
- Browser proof drives a DONE page, submits the new mission form, and observes the new DRAFT mission with editable CHARTER.md and SPEC.json.
