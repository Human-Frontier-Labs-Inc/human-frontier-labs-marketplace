# Distillation Checklist — docs → LLM-digestible skill content

Goal: the smallest set of high-signal lines that close the measured gap. Every extra line competes for attention and risks regression.

## The delete-test (apply to every line)
Would removing this line change model behavior on a benchmark task? 
- No → it's filler. Cut it.
- Yes → keep, and make it as short as it can be while still changing behavior.

## Load-bearing vs filler (keep the left, cut the right)
KEEP — facts the model cannot reliably infer:
- exact API signatures, argument orders, return types
- version-specific gotchas ("X is a no-op on platform Y", "API Z renamed in v6")
- named constants/thresholds WITH their rationale (never voodoo numbers)
- the one non-obvious idiom that an expert reaches for and a novice doesn't
- explicit "do NOT" lines for plausible-but-wrong moves (anti-patterns the model commits)

CUT — what the model already does:
- generic architecture advice ("separate concerns", "handle errors")
- restating language/framework basics
- motivational prose, history, "why this matters" essays
- anything true of all good code everywhere (not domain-specific)

## Pointers over copies
- Reference authoritative docs by URL/path/anchor + version; don't paste large excerpts that will drift.
- Copy only stable invariants (a fixed signature, a hardware limit) — things that won't change under you.

## Right altitude
Too low: brittle step-by-step that breaks on any variation. Too high: vague platitude. Aim for a heuristic precise enough to change the decision but flexible across instances.

## Passes after drafting
1. Cut ~30% of the words (first draft is always padded).
2. Group into a scannable checklist, not paragraphs.
3. Re-run the benchmark; if a section didn't move scores, delete it.
4. Verify every claim against the authority — a wrong load-bearing line is worse than no line (it injects a confident error). The effective-esp32 v1 failure was exactly this: confident AVR-isms that don't apply to ESP32.
