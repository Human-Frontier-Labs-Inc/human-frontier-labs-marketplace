// Reusable, config-driven skill benchmark. ONE script for every domain & persona.
// Invoke: Workflow({ scriptPath: ".../run-benchmark.js", args: <config object> })
// NOTE: args arrives JSON-encoded as a string in this runtime -> JSON.parse it.
//
// config = {
//   outDir:     string,                         // abs; generators write outDir/blind/<id>.md (mkdir -p outDir/blind first)
//   rubricPath: string,                          // abs authority rubric (NOT derived from the skill)
//   skillPath:  string|null,                     // abs domain SKILL.md for skill cells
//   role:       string,                          // e.g. "DevOps engineer", "database engineer"
//   artifact:   string,                          // what to write, e.g. "Dockerfile + any .dockerignore"
//   N:          number,                          // samples/cell (>=3)
//   tasks:      [{ id, prompts: { <variant>: "text", ... } }],   // variants e.g. operator, pm, beg, expert
//   cells:      [{ name, variant, skill:bool }]  // each cell = a (variant, skill?) pair
// }
// Returns { perCell:{name:{n,mean,dimMeans}}, gap, decisions }

export const meta = {
  name: 'run-benchmark',
  description: 'Config-driven blinded benchmark: generate (variant x skill?) cells, judge vs authority rubric, report gap + transfer/lift/no-regression decisions',
  phases: [{ title: 'Generate' }, { title: 'Judge' }],
}

const cfg = typeof args === 'string' ? JSON.parse(args) : (args || {})
const N = cfg.N || 3
const role = cfg.role || 'engineer'
const artifact = cfg.artifact || 'complete answer'

const work = []
let idx = 0
// tasks may be inline (cfg.tasks=[{id,prompts}]) or on disk (cfg.tasksPath + cfg.taskIds[]).
const taskIds = cfg.tasks ? cfg.tasks.map(t => t.id) : cfg.taskIds
for (const cell of cfg.cells) for (const tid of taskIds) for (let k = 0; k < N; k++)
  work.push({ id: `g${String(idx++).padStart(3, '0')}`, cell, task: tid, k })

phase('Generate')
const promptFor = (w) => {
  const out = `${cfg.outDir}/blind/${w.id}.md`
  const head = `You are a ${role} helping a user.`
  // frozen prompt source: read verbatim from disk (preferred) or inline
  let body
  if (cfg.tasksPath) {
    body = `\n\nRead the JSON file at ${cfg.tasksPath} — an array of {id, prompts}. Find the object with id === "${w.task}" and use its prompts["${w.cell.variant}"] field VERBATIM as the user's request (do not paraphrase or add to it).\n\nWrite your COMPLETE answer (${artifact}) to: ${out}\nReturn only "done".`
  } else {
    const t = cfg.tasks.find(x => x.id === w.task)
    body = `\n\nThe user says:\n${t.prompts[w.cell.variant]}\n\nWrite your COMPLETE answer (${artifact}) to: ${out}\nReturn only "done".`
  }
  if (w.cell.skill) return `${head} FIRST read this skill in full and apply it: ${cfg.skillPath}${body}`
  return `${head} Answer from your own knowledge ONLY. Do NOT read or use any skill, plugin, or external reference file (other than the task file named below); do not use the Skill tool.${body}`
}
await parallel(work.map(w => () => agent(promptFor(w), { label: `gen:${w.cell.name}:${w.task}:${w.k}`, phase: 'Generate' })))

phase('Judge')
const taskCtx = cfg.tasksPath
  ? `\nRead the task file ${cfg.tasksPath}; find the object with id === "${'${TASK}'}". Treat its prompts.operator as the REQUIREMENTS the design must satisfy, and its "extension" field as a future change request — for the extensibility/composition dimension, judge whether THIS design absorbs that extension cleanly or would force edits across many components. Grade only the design; do not infer or reward how it was prompted.`
  : ''
const judged = await parallel(work.map(w => () =>
  agent(`You are a strict, skeptical judge. You do NOT know how this answer was produced. Score the DECISION, not vocabulary.\nRead the authority rubric: ${cfg.rubricPath}\nRead the answer: ${cfg.outDir}/blind/${w.id}.md${taskCtx.replace('${TASK}', w.task)}\nScore every rubric dimension 0-5 and apply ALL caps/red-flags. Return ONLY:\nTOTAL=<sum>\nDIMS=<d1,d2,...>\nNOTE=<one line: biggest concrete flaw vs authority>`,
    { label: `judge:${w.id}`, phase: 'Judge' })
  .then(text => {
    const mt = /TOTAL\s*=\s*(\d+(?:\.\d+)?)/i.exec(text || '')
    const md = /DIMS\s*=\s*([0-9.,\s]+)/i.exec(text || '')
    const dims = md ? md[1].split(',').map(s => parseFloat(s.trim())).filter(x => !isNaN(x)) : []
    return { cellName: w.cell.name, total: mt ? parseFloat(mt[1]) : null, dims }
  })))

const ok = judged.filter(x => x && x.total != null)
const mean = a => a.length ? a.reduce((s, x) => s + x, 0) / a.length : null
const perCell = {}
for (const cell of cfg.cells) {
  const rows = ok.filter(x => x.cellName === cell.name)
  const nd = Math.max(0, ...rows.map(r => r.dims.length))
  perCell[cell.name] = {
    n: rows.length, mean: mean(rows.map(r => r.total)),
    dimMeans: Array.from({ length: nd }, (_, i) => mean(rows.map(r => r.dims[i]).filter(x => x != null))),
  }
}

// find canonical cells by (variant, skill)
const find = (variant, skill) => {
  const c = cfg.cells.find(c => c.variant === variant && !!c.skill === skill)
  return c ? perCell[c.name] : null
}
const M = 0.5 // within-noise margin on the rubric total
const exN = find('expert', false), exS = find('expert', true)
// gap report: per-dim expert - each naive variant (no skill)
const gap = {}
if (exN) for (const cell of cfg.cells) {
  if (cell.variant === 'expert' || cell.skill) continue
  const nv = perCell[cell.name]
  if (nv && nv.dimMeans.length === exN.dimMeans.length)
    gap[cell.variant] = exN.dimMeans.map((e, i) => +(e - nv.dimMeans[i]).toFixed(2))
}
// decisions per naive variant that has both skill & noskill cells
const decisions = {}
const variants = [...new Set(cfg.cells.map(c => c.variant))].filter(v => v !== 'expert')
const bar = exN ? exN.mean : (typeof cfg.expertBar === 'number' ? cfg.expertBar : null)
for (const v of variants) {
  const vN = find(v, false), vS = find(v, true)
  if (!vN || !vS) continue
  decisions[v] = {
    naive: vN.mean, skill: vS.mean, expertBar: bar,
    transfer: bar != null ? (vS.mean >= bar - M) : null,
    lift: +(vS.mean - vN.mean).toFixed(2),
  }
}
const noRegression = (exN && exS) ? (exS.mean >= exN.mean - M) : null

log(cfg.cells.map(c => `${c.name}=${perCell[c.name].mean != null ? perCell[c.name].mean.toFixed(1) : 'NA'}`).join(' '))
return { perCell, gap, decisions, noRegression, N }
