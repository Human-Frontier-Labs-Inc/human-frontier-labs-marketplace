# opencode-harness

Set up and use the **OpenCode "zen" model harness** in any project — route agent work to cheaper models by capability (`fast` / `reasoning-heavy` / `code-generation`) to spare Claude's token budget, with Claude orchestrating and validating.

## The one idea
**Route by capability, validate the output, keep Claude as the controller.** Blind delegation to the fast model costs more than it saves.

## Setup (one command)
`/opencode-harness setup` (or run `skills/opencode-harness/scripts/setup.sh`). It checks `OPENCODE_API_KEY`, checks the `opencode` CLI, writes `~/.config/vinay-agent/config.toml` with the capability profiles, and tests both models end-to-end.

Prereqs it flags if missing: an `OPENCODE_API_KEY` (opencode.ai; keep it out of any repo) and the `opencode` CLI (`curl -fsSL https://opencode.ai/install | bash`).

## Use
- `/opencode-harness ask reasoning-heavy "<prompt>"` — call a capability profile.
- Profiles: `fast`→kimi-k2.6, `reasoning-heavy`→glm-5.2, `code-generation`→glm-5.2.

## What's inside
- `skills/opencode-harness/SKILL.md` — the harness, profiles, edge cases, the routing rule.
- `skills/opencode-harness/scripts/setup.sh` — wire + e2e-test the harness.
- `skills/opencode-harness/scripts/ask.sh` — call a profile by capability.
- `skills/opencode-harness/references/model-routing.md` — **measured** per-task routing + honest token-savings findings.
- `commands/opencode-harness.md` — the `/opencode-harness` slash command.

## Built by dogfooding
This skill was built using the harness it documents — design reasoning routed to glm-5.2, a code-gen task raced on both models, Claude orchestrating. The measured result (incl. where the fast model failed) is in `benchmarks/RESULTS.md` and the skill's `references/model-routing.md`.
