# Model routing — measured findings (dogfooded)

This skill was built **using the harness it documents**: design reasoning routed to glm-5.2, a code-generation task raced on both kimi-k2.6 and glm-5.2, Claude orchestrating + finalizing. Below is what actually happened — measured, not assumed.

## What each model did (same prompts, real calls)

| task | model | tokens (prompt/compl) | result |
|---|---|---|---|
| Edge-case design reasoning | glm-5.2 | 327 / 1800 | Good substance; but leaked its full chain-of-thought into the output and ran to the token cap before a clean finish. Usable as **raw material**, not as a finished artifact. |
| Generate `setup.sh` | kimi-k2.6 (fast) | 381 / 2200 | **Unusable.** Leaked ``` fences, dumped its entire reasoning monologue into the file, hit the cap (truncated), **failed `bash -n`**. |
| Generate `setup.sh` | glm-5.2 (code-gen) | 385 / 2155 | **Clean.** Valid syntax, complete, idempotent, even added `\|\| status="000"` robustness. Ran end-to-end after a Claude review pass. The shipped `scripts/setup.sh` is this draft, validated. |

## The routing rules (use this, it's measured)

- **`fast` → kimi-k2.6** — short, structured, latency-sensitive work: triage, classification, yes/no checks, simple lookups/transforms. **Do not** use it for code generation or any "produce a clean artifact" task — here it ignored "output only the script," leaked reasoning, and produced invalid bash.
- **`reasoning-heavy` / `code-generation` → glm-5.2** — multi-step reasoning, edge-case analysis, first-draft code/scaffolding. Produces usable output. Still leaks some chain-of-thought, so expect a strip/validate pass. (The config maps `code-generation → glm-5.2`, and the benchmark confirms it — do **not** reroute code-gen to the fast model.)
- **Claude → orchestrator + finalizer** — decompose the task, route the chunks, then produce/validate the shippable artifact (tight prose, runnable code that passes `bash -n` / tests). Fall back to Claude when: output must be production-clean first try, the task needs tool use / file ops / running-and-verifying, or a cheap model's output fails validation.

## Both cheap models share two failure modes
1. **They leak chain-of-thought** into the output and ignore "output ONLY X." Route to them for *content*, not *final formatting*.
2. **They run to the token cap** when reasoning, so a hard `max_tokens` can truncate the actual answer. Give headroom or ask for terse output explicitly.

## Token savings — the honest version
~7.4k tokens were routed to the OpenCode endpoint instead of Claude (off Claude's weekly cap). **But only ~4.7k were useful** — kimi-k2.6's ~2.6k code-gen attempt was unusable and would have needed full Claude rework.

The lesson: **savings are real via the orchestrator pattern** — route reasoning + first-draft code to glm-5.2, have Claude finalize/validate — **not via blind delegation.** "Send everything to the fast model" cost more here than it saved (you pay for the fast model's tokens *and* still pay Claude to redo it). Route by capability, validate the output, keep Claude as the controller.
