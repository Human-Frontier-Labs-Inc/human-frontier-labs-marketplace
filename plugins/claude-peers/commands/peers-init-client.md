---
description: Initialize this machine as a client of an existing broker
argument-hint: "[broker-url]"
allowed-tools: Bash
---

The user wants to connect this machine to an existing claude-peers broker at `$ARGUMENTS`.

If `$ARGUMENTS` is empty, ask the user for the broker URL before running anything (expected form: `http://<host>:7899`).

Run:

```
bash ${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.sh init client "$ARGUMENTS"
```

That generates `~/.config/claude-peers/identity.pem` + `identity.pub` and writes a client config pointing at the broker.

After it completes, the client still needs a UCAN token. Walk the user through:

1. Copy the public key from this machine to the broker machine. Example: `scp ~/.config/claude-peers/identity.pub broker-host:/tmp/my-client.pub`
2. On the broker machine, issue a token:
   ```
   claude-peers issue-token --ttl 30d /tmp/my-client.pub peer-session
   ```
   `--ttl 30d` avoids the 24h rotation treadmill. Shorter TTLs work; the client auto-refreshes before expiry.
3. Copy the JWT the broker prints back to this machine and save it:
   ```
   claude-peers save-token <jwt>
   ```
4. Verify with `/peers-status`. If this session appears in the peer list, the handshake worked.

If `$1` is empty or not a URL, ask the user for the broker URL before running the init command.
