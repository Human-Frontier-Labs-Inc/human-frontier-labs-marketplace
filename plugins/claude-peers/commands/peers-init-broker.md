---
description: Initialize this machine as the claude-peers broker (generates keys + root token)
allowed-tools: Bash
---

The user wants this machine to host the claude-peers broker. Run:

```
bash ${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.sh init broker
```

That generates the UCAN keypair and root token under `~/.config/claude-peers/` and writes the default `config.json`. If keys already exist the command is safe to re-run -- it won't overwrite them.

After it completes, tell the user:

1. The broker process still needs to be started. Run `claude-peers broker` in a terminal to start it in the foreground, or wrap it as a systemd user unit for persistence. Example unit file at `~/.config/systemd/user/claude-peers-broker.service`:

   ```
   [Unit]
   Description=claude-peers broker

   [Service]
   ExecStart=%h/.local/bin/claude-peers broker
   Restart=on-failure

   [Install]
   WantedBy=default.target
   ```

   Then `systemctl --user enable --now claude-peers-broker`.

2. Other machines on the network can now join as clients using `/peers-init-client http://<this-host>:7899` followed by a token exchange. See the `claude-peers-onboarding` skill for the full flow.

Do not edit the user's shell or systemd config files on their behalf. Show the snippets and let them decide.
