#!/usr/bin/env bash
# Own your tmux sessions deterministically + coordinate natively.
# Sessions you create are namespaced  cc-[<CC_TOK>-]<label>-<rand>  so "is this mine?"
# is a grep, not a guess. Set CC_TOK (e.g. your agent name) for per-agent isolation on a
# box shared by several cc-using agents; without it, cc- is a shared scratch namespace.
#   new <label> <cmd...>  -> creates namespaced session, prints "<session> <%pane_id>"
#   wait <session>        -> block until that session's command exits (wait-for, latched)
#   status <session>      -> read its @status (running|done)
#   mine                  -> list only your sessions
#   clean [label]         -> kill only your sessions (optionally just one label)
set -euo pipefail
PRE="cc-${CC_TOK:+$CC_TOK-}"
sub="${1:-}"; shift || true
case "$sub" in
  new)
    label="${1:?usage: cc-tmux new <label> <cmd>}"; shift
    s="${PRE}${label}-$RANDOM"
    # everything in-pane = race-free. The user cmd runs in a SUBSHELL so its own `exit`
    # can't skip the completion signal; we record the real exit code into @status (done:<rc>);
    # remain-on-exit keeps the session readable (status/output) until you clean it.
    cmd="tmux set -p remain-on-exit on; tmux set -p @status running; ( $* ); rc=\$?; tmux set -p @status done:\$rc; tmux wait-for -S ${s}-done"
    pid=$(tmux new-session -d -s "$s" -P -F '#{pane_id}' "$cmd")
    echo "$s $pid" ;;
  wait)   tmux wait-for "${1:?usage: cc-tmux wait <session>}-done" ;;
  status) want="${1:?usage: cc-tmux status <session>}"
          tmux list-panes -a -F '#{session_name} #{@status}' 2>/dev/null | awk -v s="$want" '$1==s{print $2; f=1} END{exit !f}' ;;
  out)    want="${1:?usage: cc-tmux out <session>}"  # full job output + a trailing "Pane is dead (status N...)" line = exit code
          p=$(tmux list-panes -a -F '#{session_name} #{pane_id}' 2>/dev/null | awk -v s="$want" '$1==s{print $2; exit}')
          [ -n "$p" ] && tmux capture-pane -p -S - -t "$p" || { echo "no such session: $want" >&2; exit 1; } ;;
  mine)   tmux ls -F '#{session_name}' 2>/dev/null | grep "^${PRE}" || true ;;
  clean)  tmux ls -F '#{session_name}' 2>/dev/null | grep "^${PRE}${1:-}" | while read -r x; do tmux kill-session -t "=$x" && echo "killed $x"; done ;;
  *) echo "usage: cc-tmux {new <label> <cmd>|wait <session>|status <session>|mine|clean [label]}  (set CC_TOK for per-agent isolation)" >&2; exit 2 ;;
esac
