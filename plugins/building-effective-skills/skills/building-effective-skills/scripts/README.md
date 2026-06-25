# Programmatic pipeline — turnkey scripts

The gather-expertise and test-native-output steps are scripts, not hand-rolled per domain. `args` to the Workflow scripts is delivered JSON-encoded; they `JSON.parse` it.

## 0. gather.sh — authority docs -> clean markdown (pith)
```
scripts/gather.sh <urls.csv> <out-dir> [workers]
```
Pipes a list of authority URLs (language reference, style/API guidelines, framework docs) through **pith** into `<out-dir>/authority.md` + `authority.json`. Comprehensive, free, parallel. Build the rubric (step 1) from this local corpus, not the live web. Needs pith (`pip install pith`, or set `PITH_REPO`/`PITH_BIN`).

## 1. setup-domain.js — gather authority + define tests
Builds the authority rubric (from real docs) and the frozen task prompts (persona naive variants + expert).
```
Workflow({ scriptPath: ".../setup-domain.js", args: {
  outDir, nTasks: 4, personas: ["operator","pm","beg"],
  rubricInstruction: "<what to grade, which authority docs, 5 dims + caps>",
  taskInstruction:   "<which tasks to define>"
}})
```
Writes `outDir/RUBRIC.md`; returns `{ rubricSummary, tasks:[{id,difficulty,prompts:{operator,pm,beg,expert}}] }`.
Save tasks to `outDir/tasks.json`.

## 2. run-benchmark.js — test native output, blind, vs authority
One script, any domain/persona. A cell = a `(variant, skill?)` pair; a persona is just a variant.
```
mkdir -p <outDir>/blind   # first
Workflow({ scriptPath: ".../run-benchmark.js", args: {
  outDir, rubricPath, skillPath, role:"DevOps engineer", artifact:"Dockerfile + .dockerignore", N:3,
  expertBar: 24.0,                       // optional: skip expert cells if already measured
  tasks: [{ id, prompts: { operator:"...", expert:"...", ... } }],
  cells: [
    {name:"op_noskill", variant:"operator", skill:false},
    {name:"op_skill",   variant:"operator", skill:true},
    {name:"expert_noskill", variant:"expert", skill:false}
  ]
}})
```
Returns `{ perCell, gap, decisions, noRegression }`:
- `gap[variant]` = per-dimension (expert − naive) — **read this BEFORE building**; if all ≈0, do not build.
- `decisions[variant]` = `{naive, skill, expertBar, transfer, lift}` per persona.
- `noRegression` = expert+skill ≥ expert+noskill.

## Flow
1. `setup-domain.js` → rubric + tasks.
2. `run-benchmark.js` with only the noskill cells (or full) → read `gap`. **If no gap, stop — don't build.**
3. Build the skill to the measured gap.
4. `run-benchmark.js` with skill cells → check `decisions[*].transfer` and `noRegression`.
