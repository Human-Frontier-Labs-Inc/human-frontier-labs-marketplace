---
description: Show the broker status and the current peer list
allowed-tools: Bash
---

Live broker status (pre-rendered):

!`bash ${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.sh status`

Show this output to the user. If the output indicates the broker is unreachable (connection refused, no such host, or empty), suggest they verify the `broker_url` in `~/.config/claude-peers/config.json` and confirm the broker process is running.
