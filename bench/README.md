# Efficacy harness

`run_efficacy.py` compares normal agent behavior, a strong prompt-only loop, and full Signoff under the same command template and timeout. It copies each fixture, invokes the agent, then runs hidden checks after the agent exits.

The bundled manifest is an execution example, not evidence of efficacy and not a secret benchmark. For publishable results, keep manifests/evaluators outside agent access, preregister tasks and thresholds, include every failed install/timeout/stop, and report cost and model settings.

See `docs/benchmarks.md`.
