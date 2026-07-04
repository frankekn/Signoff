# Product

## Register

product

## Users

Signoff is for people who delegate repository work to coding agents and need a local, inspectable way to decide whether the work is actually ready. They are usually inside a Git repository, looking for the next legal action, the current proof state, and the artifacts that explain why a mission can or cannot be signed off.

## Product Purpose

Signoff wraps a coding agent with an evidence-first approval layer. The product keeps the user outcome fixed, turns it into verifiable artifacts, locks each revision, bounds implementation scope, executes real verification commands, requires independent review, and records the resulting evidence in receipts. Success means the UI makes the current state, next action, evidence, and limits obvious without asking the user to trust agent prose.

## Brand Personality

Strict, local-first, evidence-bound. The interface should feel like a serious control room for proof, not a marketing dashboard or a chat assistant.

## Anti-references

Do not look like a generic AI agent chat room, model router, IDE clone, workflow canvas, or SaaS landing page. Avoid decorative agent metaphors, celebratory completion language without evidence, fake consensus visuals, and UI that hides receipt state behind optimistic status copy.

## Design Principles

- Show the legal state before the available action.
- Make evidence and receipts easier to inspect than to ignore.
- Keep controls narrow: one clear next move beats a menu of plausible actions.
- Separate current-mission legality from starting a new mission.
- Use visual restraint so failure, uncertainty, and scope boundaries stay legible.

## Accessibility & Inclusion

Target WCAG 2.2 AA for contrast, keyboard reachability, visible focus, and reduced-motion behavior. The UI should remain usable for color-blind users by pairing color with text, shape, or position for every state.
