# building-effective-skills — validation summary

The meta-skill was validated by dogfooding it across many domains, with blind judging against authority-grounded rubrics (never self-derived). Key results:

## Skills add value where the model's training distribution is dirty (one-shot)
Built skills and measured skill-vs-no-skill, blind, vs authority docs:
- ESP32 firmware: rewritten skill beat the no-skill baseline 12-0.
- Dockerfile security: skill+naive ≈ expert-with-no-skill (transferred expert taste to a non-expert), and rescued a "wrong-assumption beginner" from 21.4→24.0 / 25.
- GitHub Actions security: skill won head-to-head 14-2.
- Idiomatic Rust, Postgres schema: NO one-shot gap — the model was already at ceiling, even resisting wrong user suggestions. The meta-skill correctly ABSTAINS (a skill there would only regress).
Predictor: would a compiler/linter/strong canon reject the wrong version? If yes, the model already avoids it — don't build (one-shot).

## The durable value is MULTI-TURN drift prevention (the headline)
A frontier model often writes one clean file from a single prompt (no one-shot gap) yet drifts into a god-file / stringly-typed / duplicated mush over a multi-turn build — how people actually work. Measured by having a non-expert accrete a project over 4 turns, skill vs no-skill, same frontier model both arms, pairwise blind judge on the final codebase:

| stack | skill | build chains | skill wins | no-skill wins |
|---|---|---|---|---|
| Go (Bubble Tea TUI) | effective-go | 9 | 9 | 0 |
| Python (CLI tool) | python-modern-python | 4 | 4 | 0 |
| **total** | | **13** | **13** | **0** |

No-skill arms degraded into single god-files, raw dicts / bare-int state, logic duplicated across switches, exit-in-library, silent data loss. Skill arms stayed factored, typed, behavior-on-the-type, extensible.

## Conclusion
A language/framework skill's durable value on a frontier model is **drift prevention across a build** — re-applying taste every turn, the steering a non-expert can't prompt. One-shot benchmarks are blind to it. So: build effective-<stack> skills for the stacks you actually build in, gather authority from canonical docs (not your own repos), and **benchmark on the multi-turn drift axis** (`scripts/run-multiturn.js`), not one-shot.
