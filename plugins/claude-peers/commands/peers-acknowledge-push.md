---
description: Silence the push-not-enabled SessionStart nudge forever on this machine
allowed-tools: Bash
---

!`mkdir -p ~/.config/claude-peers && touch ~/.config/claude-peers/push-acknowledged && echo "Acknowledged. The push-not-enabled nudge will not fire again on this machine. Polling mode continues to work. To re-enable the nudge, remove ~/.config/claude-peers/push-acknowledged."`

Confirm to the user that the nudge is dismissed.
