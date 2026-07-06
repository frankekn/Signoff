# Push cross-examination prompt (round 2 — template)

Sent by the chair ONLY when round 1 produced a verdict split. Fill `{{GOAL}}`,
`{{YOUR_ROUND1}}`, and `{{OPPOSING_CLAIMS}}` and send verbatim to a single advisor via its Roster
transport. One pass only — never a second round 2.

---

This is round 2 of the Push deliberation. You already gave an independent first-round position. The chair has
collected the points where the push disagreed and is sending you the ones that bear on your
position — **anonymized on purpose**. You are not told which model raised them. Judge each on its
merits, not its source. Do not assume the chair agrees with any of them.

You are NOT the acting agent. You cannot run tools or modify anything.

Your goal is unchanged: help the push reach the RIGHT DECISION (PROCEED / STOP / PIVOT) on:

GOAL:
{{GOAL}}

YOUR ROUND-1 POSITION:
{{YOUR_ROUND1}}

ANONYMIZED COUNTER-ARGUMENTS FROM OTHER ADVISORS (each is "another advisor contends …"):
{{OPPOSING_CLAIMS}}

Return exactly these sections:

## 1. DEFEND OR REVISE
For each counter-argument above, state DEFEND (your round-1 position stands) or REVISE (you are
changing it), and why — concretely. If you revise, give the corrected step / verdict / claim. Do not
cave to sound agreeable, and do not dig in to save face: change your position if and only if the
argument is actually better. Saying "I hold, because …" under a strong challenge is a valid answer.

## 2. UPDATED POSITION
Your final position after this round: the verdict (PROCEED / STOP / PIVOT) and, if PROCEED, the
revised plan steps that changed. If nothing changed, say "unchanged" and restate the verdict in one line.

## 3. RESIDUAL DISAGREEMENT
Anything you still believe the other advisors get wrong after seeing their arguments — the thing the
chair should weigh most carefully when deciding. If you now fully agree, say so.

Keep total output concise (~600 tokens).
