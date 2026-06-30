# tmux coordination primitives (verified on tmux 3.6a)

The agentic "easter eggs" the default playbook misses. Recipes are copy-paste; `cc-tmux.sh` wraps the common path.

## wait-for — block on an event, zero polling
Replace `sleep`-loops + sentinel files. A job signals a channel when it exits; a waiter blocks until then.
```
# job signals on completion
tmux new-session -d -s cc-build-7f3 'go build ./... ; tmux wait-for -S cc-build-7f3-done'
# waiter blocks, returns the instant the build exits
tmux wait-for cc-build-7f3-done
```
- **The signal LATCHES** (verified 3.6a): if the job finishes before you wait, the next `wait-for` still returns immediately — no race. (Older tmux may differ; this is the load-bearing assumption.)
- N parallel jobs → one channel each; `wait-for` each in turn (or fan them out).
- Run the waiter through your Bash background/Monitor mechanism so it doesn't hold your turn.
- `-L`/`-U` give a lock channel if you need mutual exclusion between agents; rarely needed.

## Pane @options — a zero-copy status/IPC channel
Don't scrape stdout to learn a job's state. Write structured status onto the pane and read it back — no parsing, no copying.
```
tmux set -p -t %14 @status building          # the job/agent writes (any key: @status, @phase, @result…)
tmux display-message -p -t %14 '#{@status}'   # anyone reads it
```
- **Read by pane id (`%14`) or bare session name — NOT by `=name`.** The `=` exact-match prefix works for `kill-session`/`has-session` but returns empty for `display-message` reads (verified). To read by an exact session name safely, filter instead: `tmux list-panes -a -F '#{session_name} #{@status}' | awk '$1=="cc-x-7f3"{print $2}'`.
- This is how agents coordinate *through* tmux state (job → agent, agent ↔ agent) instead of shuttling text.

## Keeping a finished job readable
By default a session is destroyed when its command exits — you lose the output and exit code. Set `remain-on-exit on` (per-pane, set it from *inside* the pane before the command runs, to avoid a race) and the pane stays as "dead":
```
# inside the launched command, first thing:
tmux set -p remain-on-exit on
```
- Read the full output afterward with `capture-pane -p -S -` (full history; plain `-p` drops scrolled lines).
- The trailing `Pane is dead (status N, …)` line carries the **exit code** N.
- `cc-tmux.sh new` does all of this for you (subshell-wraps your command so its own `exit` can't skip the signal, records `done:<rc>` into `@status`).

## pipe-pane — live output stream
Tee a pane's output to a file/processor as it happens, without repeated snapshots:
```
tmux pipe-pane -t %14 -o 'cat >>/tmp/cc-7f3.log'   # toggle on; -o = only-output
tmux pipe-pane -t %14                               # toggle off
```
Use for watching a long job or feeding its output into a processor in real time.

## Control mode (-CC) — DEFERRED
A machine-readable event stream for driving many panes programmatically (`tmux -CC`). Real power for fleet-of-panes orchestration, but more than current needs — reach for it only when one-pane-at-a-time genuinely doesn't scale. Not part of the day-to-day playbook.
