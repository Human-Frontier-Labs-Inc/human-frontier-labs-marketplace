---
name: opencode-harness
description: Set up and use the OpenCode "zen" model harness in any project — route agent work to cheaper models by capability (fast / reasoning-heavy / code-generation) to save Claude's token budget, with Claude orchestrating and validating. Use when integrating OpenCode, wiring kimi-k2.6 / glm-5.2, creating ~/.config/vinay-agent/config.toml, offloading reasoning or code generation to a cheaper endpoint, or deciding which model a task should go to. Triggers on "opencode", "opencode harness", "vinay agent", "route to a cheap model", "save tokens", "kimi", "glm", "/opencode-harness".
---

# OpenCode Harness

Wire a project to the OpenCode "zen" endpoint so agent work routes to cheap models **by capability** — while Claude stays the orchestrator that finalizes and validates. Offloading reasoning and first-draft code to glm-5.2 / kimi-k2.6 spares Claude's weekly cap.

## The one idea

**Route by capability, validate the output, keep Claude as the controller.** Blind delegation to the fast model costs more than it saves — measured (`references/model-routing.md`): a code-gen task sent to kimi-k2.6 came back unusable and would have needed full Claude rework anyway. Route reasoning + first-draft code to glm-5.2, have Claude finalize.

## Setup (one command)

Run **`scripts/setup.sh`** (`--force` overwrites an existing config). It checks `OPENCODE_API_KEY`, checks the `opencode` CLI, writes `~/.config/vinay-agent/config.toml` with the capability profiles, and tests both models end-to-end (exits non-zero if a model fails).

If it halts, it tells you what's missing:
- **API key** — get one at opencode.ai. Keep it out of any repo (e.g. `~/.config/opencode/keys.env`, `source`d). The config references it by env var, never stores it.
- **opencode CLI** — `curl -fsSL https://opencode.ai/install | bash`.

## Capability profiles

| an agent REQUIRES | model | use for |
|---|---|---|
| `fast` | kimi-k2.6 | triage, classification, short structured calls |
| `reasoning-heavy` | glm-5.2 | multi-step reasoning, edge-case analysis |
| `code-generation` | glm-5.2 | first-draft code / scaffolding |

## Use it

**`scripts/ask.sh <profile> "<prompt>" [max_tokens]`** resolves the profile → model from the config and calls the endpoint:
```
scripts/ask.sh reasoning-heavy "design a retry policy for flaky uploads"
```
Needs `OPENCODE_API_KEY` in the environment. (The vinay-agent harness also reads this same config automatically.)

**Full routing guidance in `references/model-routing.md`** (measured, with token numbers). Short version: glm-5.2 for reasoning + codegen; kimi-k2.6 only for short/fast/structured work; Claude to orchestrate, finalize, and run-and-verify. **Both cheap models leak chain-of-thought and ignore "output only X"** — strip and validate their output before using it; never ship it unchecked.

## Edge cases (detection → handling)

- **No API key** — `[ -z "$OPENCODE_API_KEY" ]` → setup halts; export the key / source your keys file, re-run.
- **opencode CLI missing** — `command -v opencode` fails → install with the official script, re-run.
- **Offline / unreachable** — e2e test shows http `000` → endpoint down or you're offline; nothing to wire, fall back to Claude/local.
- **Bad key / unknown model** — http `401` / `404` → fix the key, or the model name in `config.toml`.
- **Capability ceiling → fallback** — a `fast` result that's junk, truncated, or fails validation → escalate to glm-5.2; glm-5.2 output that fails validation or needs tool use → finalize on Claude. Validation (e.g. `bash -n`, a test) is the gate, not the model's confidence.

## Pointers
- `scripts/setup.sh` — wire + test the harness.
- `scripts/ask.sh` — call a capability profile.
- `references/model-routing.md` — measured per-task routing + honest token-savings findings.
