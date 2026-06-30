# effective-tmux

Operate tmux as an **agentic multiplexer** on a live, shared machine — run and coordinate parallel background work without mangling the user's or other agents' sessions. For Claude *driving* the tmux CLI, not configuring tmux.

## The one idea
You already do the basics well (`capture-pane -p`, `-F` formats, detached parallelism). This skill fills the three things agents consistently miss on a **shared** box: **deterministic ownership, native coordination, and lifecycle.**

1. **Own your sessions deterministically** — namespace everything `cc-[<agent>-]<label>-<rand>`; only mutate `cc-` sessions; target by `=`exact-name or stable `%/$/@` IDs (a bare `-t name` is a prefix match that hits the wrong session; indices renumber); `send-keys` only to a pane you created.
2. **Coordinate with native primitives** — `wait-for` (block on a signal, zero polling, latches), pane `@options` as a zero-copy status/IPC channel — instead of `sleep`-poll + sentinel files.
3. **Lifecycle** — track via the `cc-` prefix, tear down what you spawn, report a left-running session by exact name, never `kill-server`; a "busy" file is usually your own detached session (confirm with `fuser`/`lsof` before killing).

## What's inside
- `skills/effective-tmux/SKILL.md` — the three parts, tight, examples inline.
- `skills/effective-tmux/scripts/cc-tmux.sh` — the lifecycle wrapper: `new`/`wait`/`status`/`out`/`mine`/`clean`, `CC_TOK` for per-agent isolation.
- `skills/effective-tmux/references/primitives.md` — `wait-for`, `@options` IPC, `pipe-pane` recipes (control mode deferred).

## How it was built
Built with the building-effective-skills discipline: customer interview (a heavy-tmux agent), canonical authority (tmux man page + wiki), a **measured baseline** (no-skill agents drop the ball on ownership + the coordination primitives, while already at ceiling on observation/inventory — so the skill fills only the gap), and a plan-based A/B + adversarial validation. See `benchmarks/RESULTS.md`. Every primitive verified on tmux 3.6a; the helper iterated through 5 real bug fixes.
