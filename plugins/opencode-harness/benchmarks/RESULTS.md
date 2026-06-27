# opencode-harness — dogfood benchmark

The skill was built **using the harness it documents**: design reasoning routed to glm-5.2, the same code-generation task raced on both kimi-k2.6 and glm-5.2, Claude orchestrating and finalizing. Real calls, measured tokens.

## Same prompts, real calls

| task | model | tokens (prompt/compl) | result |
|---|---|---|---|
| Edge-case design reasoning | glm-5.2 | 327 / 1800 | Good substance, but leaked full chain-of-thought and hit the token cap. Usable as raw material, not a finished artifact. |
| Generate `setup.sh` | kimi-k2.6 (fast) | 381 / 2200 | **Unusable** — leaked ``` fences, dumped its reasoning into the file, truncated at the cap, **failed `bash -n`**. |
| Generate `setup.sh` | glm-5.2 (code-gen) | 385 / 2155 | **Clean** — valid syntax, complete, idempotent. Shipped after a Claude review + a successful end-to-end run. |

## Findings (these drive the skill's routing rules)
- **code-generation → glm-5.2**, confirmed. Routing it to the "fast" model (a tempting intuition) produced invalid bash here. The config mapping is correct.
- **fast (kimi-k2.6)** is for short/structured/latency-sensitive work only — not clean-artifact generation.
- **Both cheap models leak chain-of-thought** and ignore "output only X." Route to them for content; have Claude strip + validate.
- **Claude is the orchestrator/finalizer** — decompose, route, then produce/validate the shippable artifact and run-and-verify.

## Token savings — honest version
~7.4k tokens were routed to OpenCode instead of Claude (off Claude's weekly cap), but **only ~4.7k were useful** — kimi-k2.6's code-gen attempt was unusable. The lesson: savings are real via the **orchestrator pattern** (route reasoning + first-draft to glm-5.2, Claude finalizes), **not via blind delegation** — "send everything to the fast model" cost more than it saved here.
