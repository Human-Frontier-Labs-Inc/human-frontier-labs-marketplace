---
name: building-effective-skills
description: Build, author, or improve a Claude skill that transfers real domain expertise. Use when creating a skill from authoritative docs, distilling documentation into LLM-digestible guidance, deciding what belongs in a skill, or proving a skill actually improves output. Covers the gather-distill-gap-detect-hill-climb-validate loop and the 4-cell benchmark that proves a skill transfers expert taste to a non-expert. Triggers on "build a skill", "make a skill", "improve my skill", "is this skill any good", "turn these docs into a skill".
---

# Building Effective Skills

Most skills are written by guessing what's useful and dumping it into a file. They are never measured, so nobody notices when they make output *worse* — which is the common case, because re-teaching what the model already does well overrides good instincts with rules of thumb.

This skill is the opposite discipline: a skill earns every line by closing a *measured* gap, and ships only after it proves it transfers expertise to a non-expert.

## The one idea

**A skill's only job is to close the gap between what the model produces naively and what an expert produces.** Not to re-explain the domain. The model already writes competent, compiling, idiomatic code for most of any domain. A skill that re-teaches that competence *regresses* it (rules of thumb are blunter than the model's own judgment). So:

> Measure the baseline first. Build the skill to fill only the holes. Prove it with the 4-cell benchmark.

The proof bar is not "skill beats naive." It is **skill + naive prompt ≥ expert prompt with no skill.** If a naive user with the skill can't match an expert without it, the skill is decoration.

## The loop

### Phase 1 — Gather authority (with pith)
Collect the *authoritative* sources (official language reference, style/API guidelines, framework docs, the primary spec for a principle). Not blog SEO, not StackOverflow folklore — you grade against these.
- Run **`scripts/gather.sh <urls.csv> <out-dir>`** — it pipes a list of authority URLs through **pith** into one clean markdown corpus (`authority.md`). Comprehensive and cheap; this is the gather engine.
- For a **language/framework/principle** skill, the URL list is: the reference + the official style/API guidelines (Rust API Guidelines; PEP 8 + PEP 484; the framework's own docs; the canonical statement of the principle).
- Keep the corpus on disk and reference it by path — **pointers, not copies** in your context. This same corpus builds the **grading rubric** (Phase 5) — gather once, use twice.

### Phase 2 — Detect the baseline (the step everyone skips)

**Test ONE-SHOT *and* MULTI-TURN — the most important gap is invisible one-shot.** A frontier model often writes one clean file from a single prompt (no one-shot gap) yet **drifts into a god-file / stringly-typed / duplicated mush over a multi-turn build** — which is how people actually work. Measured: effective-go showed *no* one-shot gap on Opus but won a multi-turn build 3-0 (`scripts/run-multiturn.js`). So one-shot "no gap" does NOT mean "don't build" — re-check with the drift test. The drift axis is where language/framework skills earn durable frontier value, by re-applying taste every turn (the steering a non-expert can't prompt).

**The gap predictor — for the ONE-SHOT axis only.** A skill adds *one-shot* value only where the model's *training distribution is dirty*. Quick test before you spend anything (but remember it does NOT cover drift):
- **CLEAN distribution → expect NO gap → likely abstain.** The toolchain or canon enforces correctness, so almost all training examples are right. Idiomatic Rust (the borrow checker rejects bad code), SQL schema design (well-documented canon). The model is at ceiling and *resists bad user advice*. Measured: Rust operator 24.0, even the wrong-assumption beginner 23.7 — a skill only risks regression.
- **DIRTY distribution → expect a gap → worth building.** Bad practice is rampant in the wild or weakly enforced, so the model defaults sub-optimally *and bends to wrong user suggestions*. Container security (root/`latest`/secrets everywhere), embedded gotchas, CI/CD security, "wild-west" config. Measured: Docker beginner dropped to 21.4 without a skill; the skill rescued it to 24.0.
- Heuristic: *would a compiler / linter / strong canon reject the wrong version?* If yes, the model probably already does too — abstain. If the wrong version compiles and ships all over GitHub, there's a gap.

Then confirm by measuring. Run the domain's representative tasks in **two conditions, no skill**:
- **naive prompt** — the bare task a non-expert would type.
- **expert prompt** — a domain expert's one-shot prompt with their checklist/gotchas inlined.

Read the outputs against the authority. Score each dimension. Now you know:
- where naive is already strong (4+/5) → **the skill must not touch this** — it will only do damage.
- where naive is weak but expert-prompting fixes it → **this is exactly what the skill must encode** (it's transferable taste).
- where even the expert prompt is weak → out of scope, or needs a tool/script, not prose.

Mine your failure set here: the tasks where naive actually breaks ARE your real-failure benchmark (Anthropic's "tasks from observed failures", generated honestly).

### Phase 3 — Distill (fill the holes, delete everything else) — run with ponytail
Write the skill to cover *only* the gap from Phase 2, under **ponytail** discipline (the `ponytail` skill): the laziest correct set of lines, deletion over addition. For every candidate line apply the **delete-test**: if removing it doesn't change model behavior, it's filler — cut it. The pith corpus is large on purpose; the skill is small on purpose — your job here is ruthless subtraction from corpus to gap. Prioritize facts the model cannot infer: exact signatures, version-specific gotchas, named constants, the one non-obvious idiom. Generic advice the model already follows is the enemy — it's the cargo cult that causes regressions.
- Right altitude: specific enough to guide, loose enough to be a heuristic.
- First pass after drafting: cut ~30% of the words.
- Detail in `references/distillation-checklist.md`.

### Phase 4 — Hill-climb
Add instruction *only in response to an observed failure*, never speculatively. Re-run the affected tasks after each change. If a line doesn't move the score, it doesn't belong. Keep climbing until the benchmark clears the bar — then stop adding (more lines past the bar trend toward regression).

### Phase 5 — Validate (the 4-cell benchmark)
Prove it. Full protocol in `references/benchmark-protocol.md`; harness in `scripts/`. Summary:

| | no skill | with skill |
|---|---|---|
| **naive prompt** | floor | **the load-bearing cell** |
| **expert prompt** | the bar to beat | ceiling / regression check |

Generate all 4 cells with fresh subagents, judge **blind** (order-swapped, identity hidden) against the authority rubric, repeated sampling (N≥5/cell). Pass iff:
1. **Transfer:** skill+naive ≥ expert+no-skill (within noise). *Load-bearing.*
2. **Lift:** skill+naive ≫ naive+no-skill (CI excludes 0).
3. **No regression:** expert+skill ≥ expert+no-skill (within noise).

Fail any → back to Phase 3.

## Authoring rules (apply while distilling)
- **Frontmatter:** `name` lowercase-hyphen gerund, ≤64 chars, no "claude"/"anthropic". `description` ≤1024 chars, third-person, says **what it does AND when to use**, concrete trigger keywords, deliberately pushy (the model under-triggers skills).
- **Length:** SKILL.md < 500 lines. Reference file > 100 lines → give it a TOC. References **one level deep only** (deeper breaks partial reads).
- **Progressive disclosure:** SKILL.md = procedure + judgment. Push deterministic/computational work (stats, grading, shuffles) into `scripts/`. Push long lookups into `references/`.
- **Anti-patterns** (each is a known failure — see `references/authoring-anti-patterns.md`): Windows paths; offering too many options; time-sensitive prose ("as of 2026"); inconsistent terminology; over-explaining what the model knows; voodoo constants with no rationale; unqualified MCP/tool names.

## Verification discipline (non-negotiable)
- **Never grade a skill with the skill, or with a rubric derived from the skill.** The referee is the independent authority. Self-grading and model-derived rubrics collapse human-agreement accuracy (92%→61%).
- **Two baselines, always.** Beating naive is trivial and proves nothing. Expert-no-skill is the real adversary.
- **Prove it ran.** Don't claim a result you didn't measure. Paste the scores. Agents fake "done"; a skill-builder that does is worthless.
- **Blind + order-swap the judge.** Position bias alone shifts code-judging >10%.

## The qualification bar (when is a skill "done")
A skill qualifies only when, across the domain's failure-mined tasks, blind-judged against authority with N≥5/cell: **skill+naive ≥ expert+no-skill**, **skill+naive ≫ naive+no-skill**, and **expert+skill does not regress**. Anything less is an unproven skill — ship it labeled as such, or keep climbing.

## Run it programmatically (don't hand-roll the loop)
The gather-authority and test-native-output steps are turnkey scripts — use them, don't rebuild per domain:
1. `scripts/setup-domain.js` → builds the authority rubric + frozen persona/expert task prompts.
2. `scripts/run-benchmark.js` → generates cells blind, judges vs the rubric, returns `gap` (per-dimension expert−naive), `decisions` (transfer/lift per persona), and `noRegression`.
**Read `gap` before writing the skill. If `gap` ≈ 0 on every dimension, STOP — the model is at ceiling; a skill can only regress it.** Full usage: `scripts/README.md`.

## Pointers
- `scripts/README.md` — the turnkey pipeline (setup-domain.js, run-benchmark.js).
- `references/benchmark-protocol.md` — full 4-cell spec, blinding, persona prompt definitions, decision rule.
- `references/distillation-checklist.md` — delete-test, load-bearing taxonomy, cut-30% pass.
- `references/authoring-anti-patterns.md` — the anti-pattern list with fixes + description/name examples.
