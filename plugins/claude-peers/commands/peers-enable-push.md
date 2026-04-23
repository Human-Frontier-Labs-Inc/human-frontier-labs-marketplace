---
description: Show how to enable real-time peer message push delivery
---

Explain to the user that claude-peers ships with two delivery modes:

1. **Polling mode (default):** Works out of the box once the plugin is installed. Messages from other peers are queued at the broker; Claude sees them when it calls `check_messages`. Good for occasional coordination, not great for real-time.

2. **Push mode:** Messages arrive as notifications the moment they're sent, no polling. Requires launching claude with the claude-peers development channel loaded. Two ways:

   **Option A (recommended): launch via the wrapper subcommand**
   ```bash
   claude-peers run
   ```
   This execs the real `claude` binary with the `--dangerously-load-development-channels server:claude-peers` flag injected. Pass any other claude flags after:
   ```bash
   claude-peers run --continue
   claude-peers run --as my-agent-name
   ```

   **Option B: shell alias**
   ```bash
   alias claude='claude-peers run'
   ```
   Add that to your `~/.bashrc` / `~/.zshrc` so typing `claude` always enables push.

Do NOT edit the user's shell config files for them. Show the alias line and let them paste it themselves.

The `-p`/`--print` flag is auto-excluded from channel injection by `claude-peers run` so scripted daemon calls stay clean.

Once push is active, the session's push-nudge SessionStart hook will stop firing (it detects the channel flag in the parent process's cmdline and exits silent). If the user wants to silence the nudge without enabling push, they can run `/peers-acknowledge-push`.
