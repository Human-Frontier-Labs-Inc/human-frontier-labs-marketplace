# 4-Cell Benchmark Protocol

Table of contents:
1. The four cells
2. Reproducible prompt definitions (naive vs expert)
3. Task set (failure-mined)
4. Authority rubric
5. Blinding & judging
6. Sampling & statistics
7. Decision rule
8. Common ways to fool yourself

## 1. The four cells
{naive prompt, expert prompt} × {no skill, with skill} = 4 cells.

| | no skill | with skill |
|---|---|---|
| naive | floor (what a non-expert gets today) | **load-bearing** (does the skill transfer taste?) |
| expert | the bar (what good prompting alone achieves) | ceiling / regression check |

The point of the expert-no-skill cell: it separates "the skill works" from "any scaffolding works." Beating only the naive floor proves nothing.

## 2. Reproducible prompt definitions
Freeze all prompts verbatim across all cells and iterations. Variance must come from sampling, not prompt drift.
- **Naive prompt = a real persona, not a sterile task line.** A clean "Write X for Y" overstates the floor — real non-experts don't talk like specs. Write the naive prompt in the voice of the actual target user: knows the goal and the facts (ports, files, framework), can't read code, informal, hedges or mis-names a detail ("i think these need to compile or something"), zero technique/scaffolding. All factual constraints must survive (or the task is ambiguous); all best-practice guidance must be absent. This is the honest, harder floor — and the input the skill must actually serve.
  - **Use multiple personas** for robustness: e.g. an operator ("knows the system, non-coder, informal"), a rushed/business framer (terse, outcome-only), a copy-paste beginner (literal, includes a wrong assumption). Each persona × {no skill, skill} is a cell pair. A skill that only transfers taste to one phrasing is brittle.
- **Expert prompt** = the same task + a domain expert's inlined checklist/gotchas/technique — the exact taste the skill is meant to transfer — as a one-shot prompt with NO file references. This is the adversary the skill must match. Write it honestly and well; a weak expert prompt is cheating.
- Skill cells: identical persona/expert prompt text, with the skill present for triggering. Confirm the skill actually triggered (check it was read).

## 3. Task set (failure-mined, not synthetic)
Do NOT invent "coverage" tasks. Run the naive+no-skill cell first on a broad set of representative domain tasks, read the outputs against authority, and KEEP the tasks where naive actually fails or scores low. Those real failures are the benchmark. Target ≥6 tasks/domain spanning ≥2 difficulty levels (to catch "helps hard, hurts easy" interactions). Each task gets a short reference of what a correct answer must contain.

## 4. Authority rubric
Build it from the gathered authoritative sources (Phase 1), NEVER from the skill. Per dimension, define concrete 0-5 score bands and explicit caps/red-flags (objectively wrong moves that cap a dimension). Score the *decision*, not vocabulary — right words with wrong application earn nothing. The rubric is a separate artifact a judge reads; the judge never sees the skill or which cell produced an output.

## 5. Blinding & judging
- Copy each output to a neutral file (strip any path/name that leaks the cell). Present pairs as A/B.
- **Order-swap:** alternate which cell is A vs B across tasks/iterations to cancel position bias (>10% effect on code judging).
- **Independent judge:** a fresh subagent with only the rubric + the two blind outputs. Different framing than the generator. Use a panel of ≥2-3 judges and average; divergence flags an ambiguous rubric.
- **Length control:** note output length; don't let verbosity buy points.
- **Human-proxy spot-read:** the builder reads a few outputs directly to sanity-check the judges aren't gaming the rubric. Never let the model be the only arbiter of the model.

## 6. Sampling & statistics
- N≥5 samples per cell (single sample overestimates effect — fixed-effect fallacy).
- Report per-dimension means and the cell totals, plus the spread. If means are within ~1 point on a 25-scale and overlapping, treat as "within noise" (non-inferior), not a win.
- Watch saturation: if every cell maxes the rubric, the rubric is too easy — add harder tasks or finer bands.

## 7. Decision rule
Pass iff all hold across the task set:
1. **Transfer (load-bearing):** mean(skill+naive) ≥ mean(expert+no-skill), within noise or above.
2. **Lift:** mean(skill+naive) − mean(naive+no-skill) clearly positive (CI excludes 0; large effect).
3. **No regression:** mean(expert+skill) ≥ mean(expert+no-skill), within noise or above.
Fail 1 → the skill doesn't transfer taste (most common failure; usually means it's re-teaching strengths). Fail 3 → the skill is poisoning good prompting (cargo cult). Either way: return to distillation.

## 8. Common ways to fool yourself
- Self-derived rubric (grading the skill against its own claims) → rigged. Use authority.
- Only one baseline (naive) → "scaffolding helps" ≠ "skill transfers expertise".
- Weak expert prompt → you beat a strawman. Write the expert prompt to genuinely win.
- N=1 → noise read as signal. Repeat.
- Judge sees the cell labels / file paths → leakage. Blind it.
- Skill never actually triggered in the skill cells → you measured the baseline twice.
