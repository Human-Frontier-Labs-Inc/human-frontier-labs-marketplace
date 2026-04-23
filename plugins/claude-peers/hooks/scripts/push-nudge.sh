#!/usr/bin/env bash
# SessionStart hook: nudge the user ONCE if claude-peers push delivery
# isn't active. Dismissible. Never periodic. Silent once acknowledged.
#
# Push delivery requires launching claude with the dev channel loaded --
# either directly (claude --dangerously-load-development-channels
# server:claude-peers) or via the wrapper subcommand (claude-peers run).
# Without the channel, MCP tools still work for polling but real-time
# messages don't land as push notifications.
#
# Detection strategy: walk up the process tree from this hook's PPID
# looking for a process whose argv contains the dev-channel flag. We use
# `ps -p <pid> -o args=` (POSIX) rather than /proc/<pid>/cmdline so the
# same code path works on Linux and macOS without platform-specific
# branches. Walks up to 3 hops in case the hook was invoked via a
# wrapper script or the shell spawned an intermediate process.
#
# Dismissal file: $CONFIG_HOME/claude-peers/push-acknowledged. Touched
# by the /peers-acknowledge-push slash command or manually. Presence
# silences this hook forever on this machine.

set -uo pipefail

CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
ACK_FILE="${CONFIG_HOME}/claude-peers/push-acknowledged"
if [[ -f "${ACK_FILE}" ]]; then
    exit 0
fi

# has_channel_flag returns 0 (true) iff the argv of the given PID contains
# the dev-channel marker. Returns 1 on any error or mismatch so the caller
# can keep walking up.
has_channel_flag() {
    local pid="$1"
    [[ -n "${pid}" && "${pid}" != "0" ]] || return 1
    local argv
    argv="$(ps -p "${pid}" -o args= 2>/dev/null)" || return 1
    [[ -n "${argv}" ]] || return 1
    printf '%s' "${argv}" | grep -q -- '--dangerously-load-development-channels'
}

# parent_pid prints the PPID of the given PID via ps. Portable across
# Linux and macOS. Empty output on error.
parent_pid() {
    ps -p "$1" -o ppid= 2>/dev/null | tr -d '[:space:]'
}

# Walk up the process tree. The hook's immediate parent is usually
# claude-code itself, but in case a wrapper script was involved we walk
# a few hops. Three levels is more than enough in practice.
pid="${PPID:-0}"
for _ in 1 2 3; do
    if has_channel_flag "${pid}"; then
        exit 0
    fi
    next="$(parent_pid "${pid}")"
    [[ -n "${next}" && "${next}" != "0" && "${next}" != "${pid}" ]] || break
    pid="${next}"
done

# Push not detected. Emit a one-shot systemMessage via the hook protocol.
# Claude sees this as additionalContext in its first turn and surfaces it
# if relevant. No status-bar noise, no periodic popups -- the user either
# enables push or dismisses the notice.
cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"claude-peers: push delivery is not active in this session. Other peers' messages will queue but won't arrive as real-time notifications until you check_messages. To enable push: relaunch via `claude-peers run` instead of `claude`, or add `alias claude='claude-peers run'` to your shell. To suppress this notice forever: `/peers-acknowledge-push` (or `touch ~/.config/claude-peers/push-acknowledged`)."}}
EOF

exit 0
