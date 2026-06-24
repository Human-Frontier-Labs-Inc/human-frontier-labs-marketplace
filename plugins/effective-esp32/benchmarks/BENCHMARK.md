# effective-esp32 — v2 Hill-Climb Result (full 12)

Same method as v1 (blind judge, authority rubric, A/B order alternated). v2-with was scored against the **identical** without-skill baselines, blind.

## Three-way (the headline)
| | avg /25 | record vs baseline |
|---|---|---|
| **v1 skill (original, 946 lines)** | **15.2** | 0 W · 1 T · 11 L |
| baseline (no skill) | 20.0 | — |
| **v2 skill (~150 lines)** | **24.25** | **12 W · 0 T · 0 L** |

v2 lifted **+4.25 over baseline** and **+9.05 over the original skill**. The skill went from net-negative to net-positive by *deleting* most of itself.

## Per-iteration (v2-with vs baseline, this round's blind judges)
| iter | project | baseline | v2 |
|---|---|---|---|
| 1 | sono-pix C3 | 19 | **25** |
| 2 | rgb-board C3 | 14 | **25** |
| 3 | claude-keys S3 | 19 | **24** |
| 4 | sono-pix C3 | 22 | **25** |
| 5 | rgb-board C3 | 22 | **25** |
| 6 | claude-keys S3 | 17 | **24** |
| 7 | sono-pix C3 | 18 | **25** |
| 8 | rgb-board C3 | 20 | **25** |
| 9 | claude-keys S3 | 15 | **22** |
| 10 | sono-pix C3 | 22 | **25** |
| 11 | rgb-board C3 | 16 | **24** |
| 12 | claude-keys S3 | 20 | **22** |

## Per-dimension — where the lift came from (and proof it didn't break anything)
| dim | baseline | v1 skill | **v2 skill** | note |
|---|---|---|---|---|
| memory | 4.17 | 2.33 | **4.83** | v1 *regressed* it (PROGMEM cap); v2 lifts it |
| ISR safety | 3.83 | 3.67 | **4.67** | target hole #1 — fixed (IRAM_ATTR+FromISR+yield) |
| task design | 4.25 | 3.08 | **4.75** | v1 regressed (core-pin-on-C3); v2 lifts |
| contention | 4.83 | 3.67 | **5.00** | v1 regressed (delay band-aids); v2 maxes |
| validation | 2.92 | 2.42 | **5.00** | target hole #2 — fixed (measure-before-tune, stack HWM, mA budget) |

**Zero rubric caps triggered on any v2 output across all 12.** The two targeted holes (validation 2.9→5.0, ISR 3.8→4.7) moved most; nothing regressed.

## Why it worked
v2's whole thesis: the baseline is already 4+/5 on memory/task/contention — *don't re-teach it*. v1's failure was teaching those badly (AVR-isms, C3-myths). v2 deletes all of that and adds only the two things the baseline reliably misses: exact ISR primitives and a measurement discipline. Confirms Willy's call — Claude's C++ compiles fine; what a skill can add is the taste/rigor it skips, not a re-explanation of what it already does well.

## Recommendation
Promote `SKILL_v2.md` → `SKILL.md` (jim's call — original left untouched). Consider deleting `references/effective-esp32-patterns.md` or rebuilding it as a measurement/ISR cookbook; most of its v1 content carries the same errors.
