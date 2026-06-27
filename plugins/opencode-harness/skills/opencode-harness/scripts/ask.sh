#!/usr/bin/env bash
# Call a capability profile through the OpenCode harness.
# usage: ask.sh <profile> "<prompt>" [max_tokens]
#   profile = fast | reasoning-heavy | code-generation (resolved from config.toml)
set -euo pipefail
CONFIG="$HOME/.config/vinay-agent/config.toml"
ENDPOINT="https://opencode.ai/zen/v1/chat/completions"
profile="${1:?usage: ask.sh <profile> "\""<prompt>"\"" [max_tokens]}"
prompt="${2:?usage: ask.sh <profile> "\""<prompt>"\"" [max_tokens]}"
maxtok="${3:-1024}"
[[ -n "${OPENCODE_API_KEY:-}" ]] || { echo "OPENCODE_API_KEY unset (source your keys file)" >&2; exit 1; }
[[ -f "$CONFIG" ]] || { echo "no config at $CONFIG — run setup.sh first" >&2; exit 1; }
# resolve [profiles.<profile>] -> model = "..."
model=$(awk -v p="[profiles.$profile]" '
  $0==p {f=1; next}
  f && /^\[/ {f=0}
  f && /model[[:space:]]*=/ {gsub(/.*=[[:space:]]*"|".*/,""); print; exit}
' "$CONFIG")
[[ -n "$model" ]] || { echo "unknown profile: $profile (see $CONFIG)" >&2; exit 1; }
payload=$(jq -n --arg m "$model" --arg p "$prompt" --argjson mt "$maxtok" \
  '{model:$m, messages:[{role:"user",content:$p}], max_tokens:$mt}')
curl -s "$ENDPOINT" -H "Authorization: Bearer $OPENCODE_API_KEY" -H "Content-Type: application/json" -d "$payload" \
  | jq -r '.choices[0].message.content // (.error|tostring)'
