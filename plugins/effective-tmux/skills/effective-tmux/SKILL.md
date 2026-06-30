---
name: effective-tmux
description: Operate tmux as an agentic multiplexer on a live, shared machine — run and coordinate parallel background work without disrupting the user's or other agents' sessions. Use when driving tmux non-interactively (new-session -d, send-keys, kill-session) to run long-running processes, orchestrate parallel jobs, or coordinate between agents, ESPECIALLY where the user or other agents already have tmux sessions. NOT for configuring tmux (.tmux.conf / keybindings). Triggers on tmux new-session, send-keys, kill-session, "run it in tmux", "background job in tmux", parallel jobs, driving tmux on a shared/remote box.
---

# Effective tmux (agentic multiplexing on a live box)

You already do the basics well — `capture-pane -p` to read a pane without disrupting it, `-F '#{...}'` to inventory, detached sessions for parallel work. Don't relearn those. This skill fills the three things agents consistently miss on a **shared** machine, where the user and other agents already have sessions you must not touch: **deterministic ownership, native coordination, and lifecycle.**

## 1. Own your sessions deterministically

You are a guest. Make "is this session mine?" a check, not a guess.

- **Namespace everything you create** with a unique prefix: `cc-<task>-<rand>` (e.g. `cc-test-7f3`). Then *yours* is exactly `tmux ls -F '#{session_name}' | grep '^cc-'`. **Only ever kill / rename / send-keys to `cc-` sessions. Everything else is read-only** (`capture-pane -p` is fine; nothing that mutates). On a box **other agents** share, set `CC_TOK=<your-agent-name>` so your prefix is `cc-<agent>-…` and "mine" is scoped to you, not the whole fleet's `cc-` namespace.
- **Target by exact name or stable ID — never a bare name or an index.** `tmux -t dev` is a *start-of-name* match, so it silently hits `dev-server`; pane/window indices renumber when something closes. Use `=` for an exact match (`kill-session -t =cc-test-7f3`), or capture the stable id at creation and use that:
  ```
  pid=$(tmux new-session -d -s cc-test-7f3 -P -F '#{pane_id}' 'your-cmd')
  tmux send-keys -t "$pid" 'echo hi' Enter
  ```
  Pane `%`, window `@`, and session `$` ids never change for the life of the object — they are the safe target.
- **`send-keys` is a live keyboard typing into that pane.** Only ever send to a `%pane_id` you created. A wrong target runs your command in the user's shell.

## 2. Coordinate with native primitives, not sleep-polling

The lazy default is `sleep`-poll + sentinel files. tmux has real events — use them.

- **`wait-for` — block on a signal, zero polling.** The job signals when it exits; the waiter blocks until then (the signal latches, so there's no race if the job finishes first — verified on tmux 3.6a):
  ```
  tmux new-session -d -s cc-build-7f3 'go build ./... ; tmux wait-for -S cc-build-7f3-done'
  tmux wait-for cc-build-7f3-done      # returns the instant the build exits
  ```
  N parallel jobs → one channel each, `wait-for` each in turn. Run the waiter through your Bash background/Monitor mechanism so it doesn't hold the turn.
- **Pane `@options` — a zero-copy status/IPC channel.** Don't scrape stdout to learn a job's state; write and read structured status directly:
  ```
  tmux set -p -t "$pid" @status building          # the job/agent writes
  tmux display-message -p -t "$pid" '#{@status}'   # anyone reads it — no parsing, no copy
  ```
  This is how agents coordinate *through* tmux state instead of shuttling text around.

## 3. Lifecycle — leave the server as you found it

- The `cc-` prefix is your tracker. Tear down when done:
  `tmux ls -F '#{session_name}' | grep '^cc-' | xargs -r -n1 -I{} tmux kill-session -t '={}'`
- Leaving something running on purpose (a dev server the user asked for)? Tell the user its **exact session name** so they can find and stop it.
- **Never `kill-server`** — it destroys everyone's tmux. Diagnostic: if a file or port is unexpectedly "busy" / in use (e.g. `ETXTBSY` overwriting a binary), **suspect your own detached session** holding it — `tmux ls`, kill yours, re-check before concluding the binary or code is broken. **Confirm the holder is actually yours first** (`fuser /path` or `lsof /path` → map the PID to a `cc-` session); if it isn't yours, stop and surface it — never kill a process or session you didn't start.
- **Restarting a service you don't own is still off-limits even without `kill-session`** — don't `send-keys C-c`/re-run into the user's pane either. Inspect read-only, surface to the user, let them restart it.

## scripts/cc-tmux.sh

One command for the whole discipline so you don't hand-roll it — the full job lifecycle:
`new <label> <cmd>` (namespaced session, prints `<session> <%pane_id>`, race-free `@status` + wait channel, survives exit so you can read it) → `wait <session>` (blocks until the job exits, no polling) → `status <session>` (`running` → `done:<exitcode>`) → `out <session>` (full output; last line `Pane is dead (status N…)` is the exit code) → `clean [label]` (kills only yours). `mine` lists yours. Set `CC_TOK` for per-agent isolation. Prefer it over hand-rolling.

To read a *finished* job's full output by hand, use `capture-pane -p -S -` — plain `-p` only shows the visible screen and drops scrolled lines.

## Pointers
- `scripts/cc-tmux.sh` — namespaced create / wait / status / list-mine / clean-mine.
- `references/primitives.md` — `wait-for`, `@options` IPC, and `pipe-pane` live-streaming recipes. (Control mode `-CC` is deferred — reach for it only when orchestrating a fleet of panes needs a machine-readable event stream.)
