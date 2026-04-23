---
name: onboarding
description: End-to-end setup guide for claude-peers -- broker vs client decision, UCAN token exchange, per-project agent identity files, push vs polling delivery.
when_to_use: Activate whenever the user mentions setting up peers, connecting Claude Code sessions across machines, configuring a fleet, seeing "claude-peers" entries in /mcp, UCAN token errors, agent name collisions, broker init, or just installed the claude-peers plugin. Also trigger on phrases like "peer network", "multi-agent Claude", "connect my Claudes", "claude-peers broker", "how do I give this session a name", or when a user pastes a claude-peers error. Prefer this skill over generic troubleshooting whenever claude-peers is implicated.
---

# claude-peers onboarding

This skill guides a user through setting up claude-peers end-to-end. It covers the mental model, installation steps, and common troubleshooting.

## Mental model

claude-peers turns a set of Claude Code sessions on one or more machines into a named peer network. Sessions can see each other, send messages, share context via a small markdown memory blob, and claim stable identities that survive restarts.

Three process roles exist:

- **Broker** — one per network. A long-running daemon that holds the peer registry, routes messages, stores shared memory, and issues UCAN tokens. Usually runs on an always-on machine (server, homelab, VPS).
- **MCP server** — one per Claude Code session. Spawned automatically by Claude Code when the plugin's `.mcp.json` loads. Registers the session with the broker, surfaces the `peers` MCP tools inside Claude, handles message push.
- **CLI** — the same `claude-peers` binary invoked with non-`server` subcommands for admin work (init, issue-token, status, etc).

All three are the same binary; the subcommand picks the mode.

## Install flow

### Step 1 — install the plugin

The user already did this (`/plugin install claude-peers@human-frontier-labs-marketplace`). The plugin's bootstrap.sh will download the correct binary from GitHub releases on first use.

If the user wants to use their own locally-built binary (e.g., from `go install github.com/WillyV3/claude-peers-go@latest`), they can set `CLAUDE_PEERS_BIN=$(which claude-peers)` in Claude Code's env and the bootstrap will exec that instead of downloading.

### Step 2 — decide broker location

Ask the user: do you already have a claude-peers broker running anywhere? Possibilities:

- **Yes, on another machine** → they'll set up this machine as a client pointing at the existing broker. Go to Step 3b.
- **No, this machine will host the broker** → most common for single-machine use or a user setting up the first node of a fleet. Go to Step 3a.
- **Unsure** → ask where they run persistent services (homelab, always-on Mac, VPS). The broker should live there, not on a laptop that sleeps.

### Step 3a — this machine is the broker

```bash
/peers-init-broker
```

That generates `~/.config/claude-peers/` with keypair + root token. Then tell the user to start the broker:

```bash
claude-peers broker &
```

For a real deployment, wrap that in a systemd user unit so it survives reboots. Example unit file belongs in `~/.config/systemd/user/claude-peers-broker.service`:

```
[Unit]
Description=claude-peers broker

[Service]
ExecStart=%h/.local/bin/claude-peers broker
Restart=on-failure

[Install]
WantedBy=default.target
```

Enable with `systemctl --user enable --now claude-peers-broker`.

### Step 3b — this machine is a client

```bash
/peers-init-client http://<broker-host>:7899
```

That generates `~/.config/claude-peers/identity.pem` + `identity.pub` and writes a client config pointing at the broker. Then the user needs a UCAN token issued by the broker:

1. Copy `~/.config/claude-peers/identity.pub` from this machine to the broker machine
2. On the broker, run:
   ```bash
   claude-peers issue-token --ttl 30d /path/to/identity.pub peer-session
   ```
   (`--ttl 30d` avoids the 24h rotation treadmill. Shorter TTLs are fine; the client will auto-refresh before expiry.)
3. Paste the JWT the broker prints back into this machine's terminal
4. Save it:
   ```bash
   claude-peers save-token <jwt>
   ```

Verify with `/peers-status`. If the user sees themselves in the peer list, the auth handshake worked.

### Step 4 — claim an agent name (optional but recommended)

By default sessions are *ephemeral* — they appear in the peer list but aren't addressable by name. To give a session a stable name, drop a file at the project root:

```bash
echo my-agent-name > ~/projects/my-project/.claude-peers-agent
```

Any Claude Code session launched from that directory (or any subdirectory) will auto-register as `my-agent-name`. The MCP server walks up from cwd toward `$HOME` looking for the file.

Three ways to set identity, in priority order:
1. `--as <name>` flag on `claude-peers run`
2. `CLAUDE_PEERS_AGENT=<name>` env var
3. `.claude-peers-agent` file in cwd or any ancestor up to `$HOME`

Names are globally unique while held. If two sessions try to claim the same name, the second falls back to ephemeral mode with a warning (T6). Pick distinct names per project / role.

### Step 5 — enable push (optional)

Without push, messages still work — they queue at the broker and drain when Claude calls `check_messages`. With push, messages arrive as notifications the instant they're sent.

Push requires launching claude with the dev channel loaded. Use the wrapper:

```bash
claude-peers run
```

Or set an alias:

```bash
alias claude='claude-peers run'
```

See `/peers-enable-push` for details. The plugin's SessionStart hook will nudge the user once per session until push is enabled OR the user dismisses it via `/peers-acknowledge-push`.

## Common pitfalls

- **"claude-peers · ✘ failed" in /mcp** — bootstrap failed to download the binary. Check network, check that github.com/WillyV3/claude-peers-go/releases/latest exists, or set `CLAUDE_PEERS_BIN` to a locally-installed binary.
- **Session not visible to other peers** — check the broker URL in `~/.config/claude-peers/config.json`. Check `/peers-status`. If list is empty, broker isn't reachable or token is expired.
- **Agent name not taking** — verify the `.claude-peers-agent` file is on the walk-up path from cwd to `$HOME`. Run `/peers-status` and look for this session's row marked `← this session`; check what name it registered as.
- **Token expired** — the MCP server auto-refreshes via `/refresh-token` before expiry. If it's been offline for longer than the token TTL, the user needs to manually refresh or get a new token issued.

## Tool surface in Claude

Once the plugin is loaded, Claude has these MCP tools under `mcp__peers__*`:

- `list_peers` — see all sessions on the network, current session marked `← this session`
- `send_message(to, message)` — send to an agent name (preferred) or session ID
- `check_messages` — drain queued messages (fallback; push is normal path)
- `set_summary` — set a short summary visible to other peers
- `claim_agent_name(name)` — claim a stable name mid-session (no restart needed)

The MCP server also injects a fleet context snapshot at session start, so Claude knows who's online and what they're doing from turn 1.
