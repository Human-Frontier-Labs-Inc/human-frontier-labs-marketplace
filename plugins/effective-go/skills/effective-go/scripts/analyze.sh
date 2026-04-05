#!/usr/bin/env bash
set -uo pipefail

# analyze.sh - Grade Go source files against Effective Go patterns.
# Requires: bash, go toolchain, standard unix tools (grep, awk, wc).
# Usage: ./analyze.sh <directory-of-go-files>
# Outputs: JSON report to stdout. All diagnostic noise goes to stderr.

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <directory-of-go-files>" >&2
    exit 1
fi

TARGET_DIR="$(cd "$1" && pwd)"

# Collect all Go files up front using find
mapfile -t all_go_files < <(find "$TARGET_DIR" -name '*.go' -type f | sort)

if [[ ${#all_go_files[@]} -eq 0 ]]; then
    echo "No .go files found in $TARGET_DIR" >&2
    exit 1
fi

mapfile -t non_test_go_files < <(find "$TARGET_DIR" -name '*.go' -not -name '*_test.go' -type f | sort)

# --- Work in a temp copy so we don't pollute the source directory ---
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

# Copy only Go files, preserving subdirectory structure
for f in "${all_go_files[@]}"; do
    rel="${f#"$TARGET_DIR"/}"
    dest_dir="$WORK_DIR/$(dirname "$rel")"
    mkdir -p "$dest_dir"
    cp "$f" "$dest_dir/"
done

# Also copy go.mod/go.sum if they exist
[[ -f "$TARGET_DIR/go.mod" ]] && cp "$TARGET_DIR/go.mod" "$WORK_DIR/"
[[ -f "$TARGET_DIR/go.sum" ]] && cp "$TARGET_DIR/go.sum" "$WORK_DIR/"

# --- Ensure go module exists for build/vet ---
if [[ ! -f "$WORK_DIR/go.mod" ]]; then
    # Detect a reasonable module name from the first package declaration
    pkg_name=""
    for f in "${non_test_go_files[@]}"; do
        pkg_name=$(grep -m1 '^package ' "$f" 2>/dev/null | awk '{print $2}') || true
        [[ -n "$pkg_name" ]] && break
    done
    mod_name="analysis/${pkg_name:-target}"
    (cd "$WORK_DIR" && go mod init "$mod_name") >/dev/null 2>&1 || true
fi

# Try to resolve dependencies
(cd "$WORK_DIR" && go mod tidy) >/dev/null 2>&1 || true

# --- Compilability ---
compiles=true
build_output=""
build_output=$(cd "$WORK_DIR" && go build ./... 2>&1) || compiles=false

vet_clean=true
vet_warnings=0
vet_output=""
vet_output=$(cd "$WORK_DIR" && go vet ./... 2>&1) || vet_clean=false
if [[ "$vet_clean" == "false" && -n "$vet_output" ]]; then
    # Count non-empty lines as warnings
    vet_warnings=$(echo "$vet_output" | grep -c '[^[:space:]]') || vet_warnings=0
fi

# --- Helper: safe grep count that never fails the script ---
grepcount() {
    grep -c "$@" 2>/dev/null || printf '0'
}

# --- Anti-pattern: os.Exit outside main.go ---
os_exit_outside_main=0
for f in "${non_test_go_files[@]}"; do
    if [[ "$(basename "$f")" != "main.go" ]]; then
        n=$(grepcount 'os\.Exit' "$f")
        os_exit_outside_main=$((os_exit_outside_main + n))
    fi
done

# --- Anti-pattern: Get-prefix getters (methods with Get prefix) ---
get_prefix_getters=0
for f in "${non_test_go_files[@]}"; do
    n=$(grep -cE 'func\s+\([^)]+\)\s+Get[A-Z]' "$f" 2>/dev/null) || n=0
    get_prefix_getters=$((get_prefix_getters + n))
done

# --- Anti-pattern: hand-rolled sort ---
# Look for array swap patterns (a[i], a[j] = a[j], a[i]) in files with 2+ for-loops
hand_rolled_sort=false
for f in "${non_test_go_files[@]}"; do
    has_swap=$(grep -cE '\[[a-zA-Z_]+\]\s*,\s*\S+\[[a-zA-Z_]+\]\s*=' "$f" 2>/dev/null) || has_swap=0
    if [[ $has_swap -gt 0 ]]; then
        for_count=$(grep -cE '^\s*for\s' "$f" 2>/dev/null) || for_count=0
        if [[ $for_count -ge 2 ]]; then
            hand_rolled_sort=true
            break
        fi
    fi
done

# --- Anti-pattern: silent error discard ---
# Match `, _ :=` or `, _ =` or standalone `_ = expr` but NOT `_ = fmt.`
silent_error_discard=0
for f in "${non_test_go_files[@]}"; do
    # Extract all lines matching error-discard patterns
    # Then exclude the intentional fmt ones, count what remains
    all_matches=$(grep -nE '(,\s*_\s*:?=|^\s*_\s*=\s*[a-zA-Z])' "$f" 2>/dev/null) || true
    if [[ -n "$all_matches" ]]; then
        # Filter out intentional fmt discards
        filtered=$(echo "$all_matches" | grep -vE '_ = fmt\.') || true
        if [[ -n "$filtered" ]]; then
            n=$(echo "$filtered" | wc -l)
            silent_error_discard=$((silent_error_discard + n))
        fi
    fi
done

# --- Anti-pattern: raw string enums ---
# switch on a variable with 3+ string literal cases, but no `type X string` in the file
raw_string_enums=false
for f in "${non_test_go_files[@]}"; do
    has_switch=$(grep -cE '^\s*switch\s+\w+' "$f" 2>/dev/null) || has_switch=0
    if [[ $has_switch -gt 0 ]]; then
        string_cases=$(grep -cE '^\s*case\s+"[^"]*"' "$f" 2>/dev/null) || string_cases=0
        if [[ $string_cases -ge 3 ]]; then
            type_defs=$(grep -cE '^\s*type\s+\w+\s+string' "$f" 2>/dev/null) || type_defs=0
            if [[ $type_defs -eq 0 ]]; then
                raw_string_enums=true
                break
            fi
        fi
    fi
done

# --- Anti-pattern: string-typed ports ---
# Port/Addr fields declared as string in structs
string_typed_ports=false
for f in "${non_test_go_files[@]}"; do
    if grep -qEi '(Port|Addr)\s+string' "$f" 2>/dev/null; then
        string_typed_ports=true
        break
    fi
done

# --- Metrics ---
total_lines=0
for f in "${all_go_files[@]}"; do
    n=$(wc -l < "$f")
    total_lines=$((total_lines + n))
done

num_files=${#all_go_files[@]}

# Count distinct packages
packages=0
if [[ ${#all_go_files[@]} -gt 0 ]]; then
    packages=$(grep -rh '^package ' "${all_go_files[@]}" 2>/dev/null | sort -u | wc -l) || packages=0
fi

# Count interfaces and their methods using awk
interfaces_json="["
first_iface=true
for f in "${non_test_go_files[@]}"; do
    # Find all interface definitions in this file
    iface_lines=$(grep -nE 'type\s+\w+\s+interface\s*\{' "$f" 2>/dev/null) || true
    [[ -z "$iface_lines" ]] && continue

    while IFS= read -r match_line; do
        iface_name=$(echo "$match_line" | grep -oE 'type\s+\w+\s+interface' | awk '{print $2}') || true
        [[ -z "$iface_name" ]] && continue

        # Count methods in interface body using awk
        method_count=$(awk -v name="$iface_name" '
            BEGIN { depth = 0; count = 0; found = 0 }
            found == 0 && $0 ~ "type[[:space:]]+" name "[[:space:]]+interface[[:space:]]*\\{" {
                found = 1
                depth = 1
                next
            }
            found == 1 && depth > 0 {
                for (i = 1; i <= length($0); i++) {
                    c = substr($0, i, 1)
                    if (c == "{") depth++
                    if (c == "}") {
                        depth--
                        if (depth == 0) {
                            print count
                            exit
                        }
                    }
                }
                stripped = $0
                gsub(/^[[:space:]]+/, "", stripped)
                gsub(/[[:space:]]+$/, "", stripped)
                if (stripped != "" && stripped !~ /^\/\//) {
                    count++
                }
            }
            END { if (found && depth > 0) print count }
        ' "$f") || method_count=0
        [[ -z "$method_count" ]] && method_count=0

        if [[ "$first_iface" == true ]]; then
            first_iface=false
        else
            interfaces_json+=","
        fi
        interfaces_json+="{\"name\":\"$iface_name\",\"methods\":$method_count}"
    done <<< "$iface_lines"
done
interfaces_json+="]"

# Count exported types (type FooBar ... where name starts uppercase)
exported_types=0
for f in "${non_test_go_files[@]}"; do
    n=$(grep -cE '^type\s+[A-Z]\w*\s+' "$f" 2>/dev/null) || n=0
    exported_types=$((exported_types + n))
done

# Comment ratio: comment lines / total lines
comment_lines=0
for f in "${all_go_files[@]}"; do
    n=$(grep -cE '^\s*(//|/\*|\*\s|\*/)' "$f" 2>/dev/null) || n=0
    comment_lines=$((comment_lines + n))
done
if [[ $total_lines -gt 0 ]]; then
    comment_ratio=$(awk "BEGIN {printf \"%.2f\", $comment_lines / $total_lines}")
else
    comment_ratio="0.00"
fi

# --- Architecture metrics ---

# has_embedding: any struct in these files contains an anonymous/embedded field
# (a line inside a struct body that is just a type with no field name, e.g. sync.Mutex or *http.ServeMux)
has_embedding=false
for f in "${non_test_go_files[@]}"; do
    # Lines that are purely a package-qualified type (optionally pointer), no field name prefix
    # Method signatures always contain () so they won't match this pattern
    n=$(grep -cE '^\s+\*?[A-Za-z][A-Za-z0-9]*\.[A-Za-z][A-Za-z0-9]*\s*$' "$f" 2>/dev/null) || n=0
    if [[ $n -gt 0 ]]; then
        has_embedding=true
        break
    fi
done

# typed_constants: count of "type X string" or "type X int" declarations (exported names only)
# These are the building blocks of enum-style typed constants in Go
typed_constants=0
for f in "${non_test_go_files[@]}"; do
    n=$(grep -cE '^\s*type\s+[A-Z][A-Za-z0-9]*\s+(string|int)\s*$' "$f" 2>/dev/null) || n=0
    typed_constants=$((typed_constants + n))
done

# lazy_init_maps: count of zero-value map design pattern
# Pattern: if x.field == nil { x.field = make(map
lazy_init_maps=0
for f in "${non_test_go_files[@]}"; do
    n=$(grep -cP 'if\s+\w+\.\w+\s*==\s*nil\s*\{\s*$' "$f" 2>/dev/null) || n=0
    if [[ $n -gt 0 ]]; then
        # Verify associated make(map on the next physical line via awk
        make_map_count=$(awk '
            /if[[:space:]]+[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*[[:space:]]*==[[:space:]]*nil[[:space:]]*\{[[:space:]]*$/ {
                found = 1
                next
            }
            found == 1 {
                if ($0 ~ /make\(map/) count++
                found = 0
            }
            END { print count+0 }
        ' "$f") || make_map_count=0
        lazy_init_maps=$((lazy_init_maps + make_map_count))
    fi
done

# constructor_count: count of New( or NewXxx( functions
constructor_count=0
for f in "${non_test_go_files[@]}"; do
    n=$(grep -cE '^func\s+New[A-Z]?[A-Za-z0-9]*\s*\(' "$f" 2>/dev/null) || n=0
    constructor_count=$((constructor_count + n))
done

# arch_packages: count of distinct package declarations (same logic as metrics.packages)
arch_packages=$packages

# --- Output JSON ---
cat <<ENDJSON
{
  "compiles": $compiles,
  "vet_clean": $vet_clean,
  "vet_warnings": $vet_warnings,
  "anti_patterns": {
    "os_exit_outside_main": $os_exit_outside_main,
    "get_prefix_getters": $get_prefix_getters,
    "hand_rolled_sort": $hand_rolled_sort,
    "silent_error_discard": $silent_error_discard,
    "raw_string_enums": $raw_string_enums,
    "string_typed_ports": $string_typed_ports
  },
  "metrics": {
    "total_lines": $total_lines,
    "files": $num_files,
    "packages": $packages,
    "interfaces": $interfaces_json,
    "exported_types": $exported_types,
    "comment_ratio": $comment_ratio
  },
  "architecture": {
    "has_embedding": $has_embedding,
    "typed_constants": $typed_constants,
    "lazy_init_maps": $lazy_init_maps,
    "constructor_count": $constructor_count,
    "packages": $arch_packages
  }
}
ENDJSON
