# claude-peers

Peer discovery and messaging between Claude Code sessions. UCAN-authenticated, multi-machine, push-delivered.

Sessions see each other, send messages, and share context automatically. Works across one machine or a fleet of machines over a private network.

**Source repo:** https://github.com/WillyV3/claude-peers-go

## What it does

- Sessions across machines register with a central broker, exchange messages, and share state
- Claim stable agent names that survive session restarts (`.claude-peers-agent` file per project)
- Real-time push delivery of peer messages (requires opt-in via `claude-peers run`)
- Polling-only fallback when push isn't enabled

## Install

```
/plugin install claude-peers@human-frontier-labs-marketplace
```

No Go toolchain required — the plugin's bootstrap.sh downloads the correct pre-built binary for your platform from GitHub releases on first use.

Supported platforms: linux-amd64, linux-arm64, darwin-amd64, darwin-arm64.

## First time setup

Run `/peers-init-broker` if this machine will host the peer broker, or `/peers-init-client <broker-url>` if you're connecting to an existing one. The `claude-peers-onboarding` skill walks Claude through the rest — just ask Claude "how do I set this up?" after installing.

## Slash commands

| Command | Purpose |
|---|---|
| `/peers-status` | Show broker status + peer list |
| `/peers-init-broker` | Set up this machine as the broker |
| `/peers-init-client <url>` | Set up this machine as a client of an existing broker |
| `/peers-enable-push` | Explain how to enable real-time push delivery |
| `/peers-acknowledge-push` | Silence the SessionStart push nudge forever |

## MCP tools

Exposed under the `peers` MCP server. Tool handles in Claude: `mcp__peers__list_peers`, `mcp__peers__send_message`, `mcp__peers__check_messages`, `mcp__peers__set_summary`, `mcp__peers__claim_agent_name`.

## Hooks

- **SessionStart push-nudge** — fires once per session if push delivery isn't detected in the current Claude launch and the user hasn't acknowledged. Injects a one-shot `additionalContext` explaining how to enable push or how to dismiss the nudge permanently. Never periodic, never shown after acknowledgement.

## Advanced: use your own locally-built binary

If you want to run claude-peers from source (e.g., developing on the project, or using a patched version), set:

```
export CLAUDE_PEERS_BIN=$(which claude-peers)
```

before launching Claude Code. The plugin's bootstrap.sh will exec your binary instead of downloading one.

## Auth model

UCAN (User Controlled Authorization Networks) — Ed25519 keypairs with JWT delegation chains. The broker mints a root token on init; each client gets a delegated token scoped to `peer-session` (full) or `fleet-read` (read-only observer). Default TTL is 24h with auto-refresh; use `--ttl 30d` at token issue to avoid the rotation treadmill for always-on peers.

Roles:
- `peer-session` — register, message, read/write memory
- `fleet-read` — list peers, read events, read memory (for observer services / dashboards)
- `fleet-write` — fleet-read + write memory
- `cli` — list peers, send messages, read events

## License

MIT. See the source repo for LICENSE and contribution details.
