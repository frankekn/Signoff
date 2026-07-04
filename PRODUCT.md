# Product

## Register

product

## Users

Traction is for people who delegate repository work to coding agents and need a local, inspectable way to move that work forward without slipping. They are usually inside a Git repository, looking for the next legal action, the current proof state, and the artifacts that explain where a run stands and what advances it one notch.

## Product Purpose

Traction is a push-pull engine around the coding agent you already use. It keeps the user outcome fixed, turns it into verifiable artifacts, runs a pre-lock Push deliberation, locks each revision, bounds implementation scope, executes real verification commands, runs a Pull review against the locked contract, and records the resulting evidence in receipts. Success means the UI makes current state, next action, evidence, and limits obvious without asking the user to trust agent prose. The deterministic gate (Grip) is an internal part of the engine, not the product's face.

## Core Principles

1. **Push-pull loop provides forward force.** Push (pre-lock planning deliberation) → lock → build → Pull (review against the locked contract) → advance one notch. Pull may only pull toward the locked target — reviewer taste and new ideas are not acceptance failures — so the loop converges instead of oscillating.

2. **A real mixture-of-agents collective provides quality.** "Three cobblers beat one mastermind" (三個臭皮匠勝過一個諸葛亮) is core, not accessory. Push and Pull default to ≥2 genuinely heterogeneous advisors (different provider/model, dispatched in parallel by the host agent; identity is constituted by dispatch, not self-reported strings). Solo mode is degraded and must be honestly marked `INSUFFICIENT_QUORUM`. Advisors are cheap by design: capped output, trimmed sealed packets, parallel dispatch. An aggregator alone synthesizes and writes artifacts (chair for Push, judge for Pull); no voting, no averaging; material conflicts resolve only by experiment, existing evidence, locked spec, or user decision. External evidence: NousResearch's HermesBench reports an opus-4.8 aggregator with a gpt-5.5 reference at 0.8202 vs 0.7607 for opus alone — their result, not Traction's.

3. **The ratchet locks in what the collective decides.** Hash-locked goal, charter, spec, and contract mean the standard agreed before implementation cannot be quietly rewritten after. Executable verification (real commands, exit codes, output hashes) is the oracle Pull compares against. This is what makes push and pull produce net forward motion instead of oscillation.

## Brand Personality

Reliable, local-first, evidence-bound. The interface should feel like a serious engine room for forward motion, not a marketing dashboard, courtroom drama, or chat assistant.

## Anti-references

Do not look like a generic AI agent chat room, model router, IDE clone, workflow canvas, or SaaS landing page. Avoid decorative agent metaphors, celebratory completion language without evidence, fake consensus visuals, refusal-as-identity framing, and UI that hides receipt state behind optimistic status copy.

## Design Principles

- Show the legal state before the available action.
- Make evidence and receipts easier to inspect than to ignore.
- Keep controls narrow: one clear next move beats a menu of plausible actions.
- Separate current-run legality from starting a new run.
- Use visual restraint so failure, uncertainty, and scope boundaries stay legible.
- Mark degraded quorum honestly; never present solo advisor dispatch as full collective quality.

## Vocabulary

| Old (Signoff) | New (Traction) |
|---|---|
| Signoff | Traction (product) |
| Court | Grip (deterministic engine that prevents slipping) |
| Mission | Run |
| Council | Push |
| Roast | Pull |
| Slice | slice (kept) |
| Receipt | Receipt (kept) |
| SIGNED OFF | terminal state word only |

Runtime mechanics are unchanged — phase machine, hash locks, subprocess verification, git-baseline scope measurement, hash-chained ledger — only the identity changed. Conformance tests prove gate behavior only; they do not establish real-agent efficacy.

## Accessibility & Inclusion

Target WCAG 2.2 AA for contrast, keyboard reachability, visible focus, and reduced-motion behavior. The UI should remain usable for color-blind users by pairing color with text, shape, or position for every state.
