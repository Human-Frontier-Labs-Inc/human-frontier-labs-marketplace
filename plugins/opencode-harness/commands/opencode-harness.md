---
description: Set up or use the OpenCode model harness (route work to cheap models by capability)
---

Use the `opencode-harness` skill. Argument: `$ARGUMENTS`

- **`setup`** (or empty): run `${CLAUDE_PLUGIN_ROOT}/skills/opencode-harness/scripts/setup.sh` and report the end-to-end test result. If it halts on a missing `OPENCODE_API_KEY` or `opencode` CLI, relay the fix it prints.
- **`ask <profile> <prompt>`**: run `${CLAUDE_PLUGIN_ROOT}/skills/opencode-harness/scripts/ask.sh <profile> "<prompt>"` (profile = `fast` | `reasoning-heavy` | `code-generation`) and return the output. Strip any leaked chain-of-thought and validate before using it.

`OPENCODE_API_KEY` must be in the environment (e.g. `source ~/.config/opencode/keys.env`). For routing guidance read the skill's `references/model-routing.md`.
