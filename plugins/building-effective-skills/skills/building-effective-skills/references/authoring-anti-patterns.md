# Authoring Anti-Patterns (with fixes)

Each is a documented failure mode. Scan your draft for these before shipping.

| anti-pattern | why it fails | fix |
|---|---|---|
| Over-explaining what the model knows | re-teaching competence overrides good instincts → regression | delete-test; cover only measured gaps |
| Confident wrong facts (cargo cult) | injects a high-confidence error worse than silence | verify every load-bearing line against authority |
| Voodoo constants | model can't adapt a number it doesn't understand | give the rationale, or make it a measured/tunable knob |
| Time-sensitive prose ("as of June 2026") | rots; misleads later | state version-pinned facts; avoid dated narration |
| Inconsistent terminology | model can't pattern-match the concept | pick one term per concept, use it everywhere |
| Offering too many options | dilutes the decision; model picks worst case | give the one recommended path; note alternatives only if a real fork |
| Windows-style paths / env assumptions | breaks on the actual runtime | POSIX paths; no hidden environment assumptions |
| Unqualified MCP/tool names | ambiguous resolution | fully-qualified names |
| SKILL.md > 500 lines | blows the always-loaded budget; dilutes | move detail to references/, keep SKILL.md procedure+judgment |
| Reference files nested >1 level | breaks `head -100` partial reads | one level deep; add a TOC if >100 lines |
| Description that only says WHAT | won't trigger | description = what it does + WHEN to use + concrete keywords, third-person, pushy |

## name / description examples
GOOD name: `building-effective-skills`, `effective-esp32` (lowercase, hyphen, no reserved words).
BAD name: `Claude_Skill_Helper`, `MySkill` (reserved word / camel / vague).

GOOD description: "Build, author, or improve a Claude skill... Use when creating a skill from authoritative docs, distilling documentation, or proving a skill improves output. Triggers on 'build a skill', 'improve my skill'." (what + when + keywords)
BAD description: "A skill for skills." (no trigger surface, no when)

## triggering test
After writing the description, list ~8 in-domain phrasings a naive user might type and ~4 adjacent-domain phrasings that should NOT trigger. Confirm the description would fire on the first set and stay quiet on the second. Under-triggering is the common failure — lean pushy.
