# Benchmark and evidence plan

Signoff must not claim that “multi-agent loops work” from demos. The evaluation separates deterministic protocol conformance from real coding efficacy.

## 1. Protocol conformance

Question: **Does the runtime enforce the protocol it claims to enforce?**

Run:

```sh
./signoff benchmark
python3 scripts/test.py
```

Required adversarial classes:

- locked charter/spec/Council/contract tampering;
- pre-existing dirty work and mid-iteration commits;
- unmapped and forbidden files;
- file and changed-line budget overflow;
- oracle failure, timeout, and repository mutation during verification;
- wrong patch hash;
- builder counted as reviewer or judge;
- duplicate/fabricated quorum metadata detectable by schema;
- silently dropped findings;
- multi-reviewer high-severity dismissal without disproof;
- PASS/FAIL conflict closed without cross-examination;
- vote/confidence used as arbitration basis;
- final contract that is not cumulative;
- completion with unresolved `ACT_ON` or insufficient proof.

A passing conformance suite proves gate behavior only. It does not prove that agents write better code.

## 2. Real-agent efficacy experiment

Question: **Under controlled budgets, does Signoff improve useful outcomes?**

### Conditions

Use the same agent/model/tool permissions in every condition:

1. `baseline` — user goal only, normal agent behavior;
2. `prompt-loop` — user goal plus a strong textual instruction to spec, review, test, and iterate, but no deterministic Signoff runtime;
3. `signoff` — full Signoff protocol;
4. ablations:
   - no immutable spec lock;
   - no path/budget scope gate;
   - no independent Roast;
   - no evidence receipts;
   - no conflict-to-experiment rule;
   - no STOP/PIVOT option.

The prompt-loop condition is essential: it tests whether the runtime adds value beyond better prompting.

### Task selection

Use a preregistered, held-out task set spanning:

- localized bugs;
- cross-file behavioral changes;
- regression-prone refactors;
- ambiguous requests containing tempting adjacent work;
- tasks with a deliberate spec gap;
- tasks where stopping is correct;
- tasks with seeded reviewer traps or misleading visible tests;
- long-horizon tasks requiring several coherent slices.

Do not tune prompts or gates on the reported test set. Separate protocol-development fixtures from efficacy tasks.

### Budget parity

For each task and condition, hold constant:

- agent/model version and reasoning setting;
- maximum wall-clock time;
- maximum model calls or token budget where the host exposes it;
- tool permissions and network access;
- starting repository commit;
- visible task description;
- retry policy.

Signoff may use multiple contexts; count their total time, tokens, and cost. Report success-per-dollar and success-per-minute, not only raw success.

### Hidden verification

The agent must not receive the final evaluator. After the run ends, the harness executes hidden commands from outside the copied project. Hidden tests should check:

- positive and negative user-visible behavior;
- regression preservation;
- forbidden files/APIs/dependencies;
- migration or rollback behavior where relevant;
- whether the original goal—not a rewritten easier goal—was satisfied.

### Primary metrics

#### Held-out task success

Binary success requires all hidden acceptance tests and policy checks to pass. Report mean and a bootstrap 95% confidence interval.

#### False-completion rate

Among runs that claim completion, the fraction failing hidden verification. This is Signoff's most important trust metric.

#### Spec-retention score

Weighted fraction of original must requirements satisfied, minus penalties for changed/omitted requirements and prohibited adjacent work. Score against the original task, not the agent-authored spec alone.

#### Regression-free success

Task success with the project's original test suite and hidden regression suite both passing.

### Secondary metrics

- human interventions per completed task;
- median time to valid first spec;
- total agent calls/tokens/cost;
- iterations to terminal state;
- changed files and changed lines;
- slop ratio: changed lines judged unnecessary for any satisfied requirement;
- scope-violation rate;
- STOP/PIVOT precision and recall on tasks with known correct action;
- reviewer defect precision/recall on seeded defects;
- dispute resolution accuracy;
- percentage of conflicts converted into a discriminating experiment;
- evidence precision: completed claims confirmed by hidden evidence;
- installation success and time across agent hosts;
- user comprehension of current state and final result.

## 3. Provisional claim threshold

A public “Signoff is effective” claim should require a preregistered held-out study with at least 100 distinct tasks and multiple seeds or repeated runs, plus all of:

- the lower bound of the 95% bootstrap interval for held-out success delta versus prompt-loop is above zero;
- false-completion rate is reduced by at least 40% relative to prompt-loop;
- spec-retention improves without more than a 2 percentage-point regression on simple localized tasks;
- success per unit cost is non-inferior, or the additional cost is explicitly justified by a material reduction in false completion;
- results include every task, failed install, timeout, STOP, PIVOT, and BLOCKED run;
- at least one independent reproduction uses the published manifest and harness.

These thresholds are provisional and should be versioned before data collection, not changed after seeing results.

## 4. Installation usability study

The iPhone-like promise needs a separate test.

Recruit users who can describe a software outcome but do not routinely configure developer tools. Give them a repository and one instruction: paste the Signoff repository URL and their goal into a supported coding agent.

Measure:

- install completion without human troubleshooting;
- time to first valid mission state;
- number of concepts the user must understand;
- whether the user can explain the final result and evidence;
- whether recovery from a failed gate is agent-driven;
- abandonment rate.

Provisional target: at least 90% successful first installation across supported hosts, median zero manual configuration edits, and no requirement for users to inspect JSON.

## 5. Harness usage

`bench/run_efficacy.py` copies each fixture into an isolated worktree, optionally installs Signoff, renders a mode-specific prompt, invokes the supplied agent argv template, and executes hidden verification after the agent exits.

Example:

```sh
python bench/run_efficacy.py \
  --manifest /path/to/private-manifest.json \
  --agent-argv-json '["codex", "exec", "--cd", "{project}", "{prompt}"]' \
  --modes baseline,prompt-loop,signoff \
  --repetitions 3 \
  --output benchmark-results/run.json
```

Supported placeholders:

- `{project}` — isolated project copy;
- `{prompt}` — rendered prompt text;
- `{prompt_file}` — path to a UTF-8 prompt file;
- `{mode}` — benchmark condition;
- `{case_id}` — manifest case identifier.
- `{python}` — the Python interpreter running the harness.

The harness cannot enforce provider-side token budgets unless the agent command exposes them. Record such host configuration in the result metadata.

## 6. Reporting rules

- publish raw per-run results and exact commit hashes;
- include timeouts, tool failures, and invalid outputs;
- distinguish protocol failure from agent task failure;
- do not use protocol-development fixtures as efficacy evidence;
- report uncertainty and effect sizes, not only win rates;
- preserve the claim boundary in every chart and release note;
- disclose model versions, dates, host settings, and benchmark contamination risks.
