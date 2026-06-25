#!/usr/bin/env bash
# Gather step of building-effective-skills: authoritative doc/style-guide URLs -> clean LLM-ready markdown.
# Uses pith (https://github.com/.../pith): URL -> markdown, free, batch, parallel.
#
# usage: gather.sh <urls-file> <out-dir> [workers]
#   urls-file: one target per line, bare URL or "label,url" (csv), # and blanks skipped
#   produces: <out-dir>/authority.md  (per-source markdown sections) and authority.json
#
# For a language/framework/principle skill, point urls-file at the AUTHORITY:
#   the language reference + the official style/API guidelines (e.g. Rust API Guidelines,
#   PEP 8 + PEP 484, Effective Go, the framework's official docs). Comprehensive in;
#   gap-detection + ponytail keep the skill itself minimal.
set -euo pipefail
URLS="${1:?usage: gather.sh <urls-file> <out-dir> [workers]}"
OUT="${2:?usage: gather.sh <urls-file> <out-dir> [workers]}"
WORKERS="${3:-6}"
mkdir -p "$OUT"
# prefer an installed pith; fall back to the local repo via uv. Override with PITH_BIN.
if [[ -n "${PITH_BIN:-}" ]]; then PITH=($PITH_BIN)
elif command -v pith >/dev/null 2>&1; then PITH=(pith)
else PITH=(uv run --project "${PITH_REPO:-$HOME/projects/pith}" pith); fi
echo "gathering $(grep -cvE '^\s*(#|$)' "$URLS") source(s) with ${PITH[*]} ..." >&2
"${PITH[@]}" --from "$URLS" --format md   --workers "$WORKERS" > "$OUT/authority.md"
"${PITH[@]}" --from "$URLS" --format json --workers "$WORKERS" > "$OUT/authority.json" 2>/dev/null || true
echo "wrote $OUT/authority.md ($(wc -l < "$OUT/authority.md") lines)" >&2
