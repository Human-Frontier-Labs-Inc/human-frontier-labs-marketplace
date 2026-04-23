#!/usr/bin/env bash
# Plugin bootstrap: ensures the claude-peers binary is present, then execs it.
#
# On first run downloads the latest release binary for the current platform
# from github.com/WillyV3/claude-peers-go into ${CLAUDE_PLUGIN_ROOT}/bin/.
# Subsequent runs reuse the cached binary -- no network hop after install.
#
# The plugin's .mcp.json calls this script with "server" as the first arg
# to start the MCP stdio server. Slash commands call it with CLI subcommands
# (status, peers, send, etc.). All args are forwarded verbatim.
#
# Developer escape hatch: if CLAUDE_PEERS_BIN is set in the environment,
# exec that directly and skip the download path. This lets someone working
# from a local dev build (e.g. `go install github.com/WillyV3/claude-peers-go`)
# use their own binary via the plugin without fighting the cached one.

set -euo pipefail

if [[ -n "${CLAUDE_PEERS_BIN:-}" ]]; then
    exec "${CLAUDE_PEERS_BIN}" "$@"
fi

if [[ -z "${CLAUDE_PLUGIN_ROOT:-}" ]]; then
    echo "claude-peers bootstrap: CLAUDE_PLUGIN_ROOT not set -- is this running under Claude Code?" >&2
    exit 1
fi

BIN_DIR="${CLAUDE_PLUGIN_ROOT}/bin"

# Detect platform. Keep in sync with the matrix in
# github.com/WillyV3/claude-peers-go/.github/workflows/release.yml.
os="$(uname -s)"
arch="$(uname -m)"
case "${os}-${arch}" in
    Linux-x86_64)  platform="linux-amd64" ;;
    Linux-aarch64) platform="linux-arm64" ;;
    Darwin-arm64)  platform="darwin-arm64" ;;
    Darwin-x86_64) platform="darwin-amd64" ;;
    *)
        echo "claude-peers bootstrap: unsupported platform ${os}-${arch}" >&2
        echo "  supported: Linux-x86_64, Linux-aarch64, Darwin-arm64, Darwin-x86_64" >&2
        echo "  workaround: go install github.com/WillyV3/claude-peers-go@latest" >&2
        echo "              then set CLAUDE_PEERS_BIN=\$(which claude-peers)" >&2
        exit 1
        ;;
esac

BIN="${BIN_DIR}/claude-peers-${platform}"

if [[ ! -x "${BIN}" ]]; then
    mkdir -p "${BIN_DIR}"
    REPO="WillyV3/claude-peers-go"

    # Resolve the latest release tag via the GitHub API. Plain curl + grep
    # so the bootstrap works on a fresh box without jq or other tooling
    # prereqs beyond bash + curl.
    latest_json="$(curl -fsSL "https://api.github.com/repos/${REPO}/releases/latest" 2>/dev/null || true)"
    tag="$(printf '%s' "${latest_json}" | grep -oE '"tag_name":[[:space:]]*"[^"]+"' | head -n1 | sed -E 's/.*"([^"]+)"$/\1/')"

    if [[ -z "${tag}" ]]; then
        echo "claude-peers bootstrap: could not resolve latest release of ${REPO}" >&2
        echo "  check GitHub is reachable, or set CLAUDE_PEERS_BIN to a locally-installed binary." >&2
        exit 1
    fi

    url="https://github.com/${REPO}/releases/download/${tag}/claude-peers-${platform}"
    echo "claude-peers bootstrap: downloading ${tag} for ${platform}..." >&2
    if ! curl -fsSL "${url}" -o "${BIN}.partial"; then
        echo "claude-peers bootstrap: download failed (${url})" >&2
        rm -f "${BIN}.partial"
        exit 1
    fi
    chmod +x "${BIN}.partial"
    mv "${BIN}.partial" "${BIN}"
fi

exec "${BIN}" "$@"
