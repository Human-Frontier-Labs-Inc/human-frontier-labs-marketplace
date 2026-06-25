# building-effective-skills

A meta-skill for building Claude skills that actually improve output — by measurement, not guesswork.

Most skills are written by guessing what's useful and dumping it in a file; they're never measured, so nobody notices when they make output *worse* (the common case — re-teaching what the model already does overrides good instincts). This skill is the opposite discipline.

## The loop
1. **Gather authority** with pith — pipe a list of canonical doc/style-guide URLs into clean markdown (`scripts/gather.sh`). Use the canonical conventions doc, never your own (possibly sloppy) repos.
2. **Detect the baseline** — find where the model already does well vs where it drops the ball. Test **one-shot AND multi-turn** (the most important gap, drift over a build, is invisible one-shot).
3. **Distill** under ponytail discipline — fill only the measured gap; delete-test every line.
4. **Hill-climb** — add instruction only in response to an observed failure.
5. **Validate** — the 4-cell benchmark (naive/expert × skill/no-skill) and the multi-turn drift test, blind, judged against the authority rubric.

## The bar
A skill qualifies only when **skill + naive prompt ≥ expert prompt with no skill** (it transfers expert taste to a non-expert), and it does not regress the expert. For language/framework skills, the durable proof is the **multi-turn drift test**: the skill keeps a non-expert's growing codebase factored and tasteful instead of drifting into a god-file.

## What it ships
- `scripts/gather.sh` — authority docs → markdown (pith; `pip install pith` or set `PITH_REPO`/`PITH_BIN`).
- `scripts/setup-domain.js` — build the authority rubric + persona/expert tasks.
- `scripts/run-benchmark.js` — blinded 4-cell absolute scoring + gap report.
- `scripts/run-pairwise.js` — head-to-head + countable signals (for subjective/elegance domains where absolute scoring saturates).
- `scripts/run-multiturn.js` — the drift test (non-expert builds over turns, skill vs no-skill).
- `references/` — benchmark protocol, distillation checklist, authoring anti-patterns.

The `.js` scripts run via the Claude Code Workflow tool (multi-agent orchestration).

## Proven
See `benchmarks/RESULTS.md`. Headline: across two stacks, a skill prevented multi-turn drift **13-0** vs no-skill on the same frontier model — while showing *no* one-shot gap. The value is in the accretion.
