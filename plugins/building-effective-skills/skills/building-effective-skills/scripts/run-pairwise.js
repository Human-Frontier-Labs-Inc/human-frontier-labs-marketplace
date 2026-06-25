// Pairwise + countable-signal benchmark — for SUBJECTIVE quality (architecture/elegance)
// where absolute rubric scoring saturates. Compares skill vs no-skill designs head-to-head, blind,
// and counts objective architecture signals. args arrives JSON-encoded -> JSON.parse.
//
// config = {
//   outDir, rubricPath, tasksPath, taskIds, skillPath, role, artifact, N,
//   variant:   "operator",          // which prompt variant to use for both cells
//   signals:   [ "name: how to count it (0-100 or an integer), good direction" , ... ]
// }
// Returns { winRate:{skill,noskill,tie}, perTask, signals:{cell:{name:mean}} }

export const meta = {
  name: 'run-pairwise',
  description: 'Head-to-head blind judging (skill vs no-skill) plus countable architecture signals',
  phases: [{ title: 'Generate' }, { title: 'Compare' }, { title: 'Signals' }],
}
const cfg = typeof args === 'string' ? JSON.parse(args) : (args || {})
const N = cfg.N || 3
const variant = cfg.variant || 'operator'
const role = cfg.role || 'engineer'
const artifact = cfg.artifact || 'design'

// opaque gen units; JS keeps the cell map (judges never see it)
const units = []
let idx = 0
for (const task of cfg.taskIds) for (const cell of ['noskill', 'skill']) for (let k = 0; k < N; k++)
  units.push({ id: `u${String(idx++).padStart(3, '0')}`, task, cell, k })

phase('Generate')
await parallel(units.map(u => () => {
  const out = `${cfg.outDir}/blind/${u.id}.md`
  const reqs = `\n\nRead the JSON file at ${cfg.tasksPath} — an array of {id, prompts}. Find id === "${u.task}" and use its prompts["${variant}"] field VERBATIM as the user's request.\n\nWrite your COMPLETE answer (${artifact}) to: ${out}\nReturn only "done".`
  const head = `You are a ${role} helping a user.`
  const p = u.cell === 'skill'
    ? `${head} FIRST read this skill in full and apply it: ${cfg.skillPath}${reqs}`
    : `${head} Answer from your own knowledge ONLY. Do NOT read or use any skill/plugin/reference file other than the task file named below; do not use the Skill tool.${reqs}`
  const opts = { label: `gen:${u.task}:${u.cell}:${u.k}`, phase: 'Generate' }
  if (cfg.genModel) opts.model = cfg.genModel   // generators on a chosen model; judges/signals stay strong
  return agent(p, opts)
}))

const find = (task, cell, k) => units.find(u => u.task === task && u.cell === cell && u.k === k)

phase('Compare')
// pair noskill_k vs skill_k per task; alternate which is shown as A to cancel position bias
const pairs = []
cfg.taskIds.forEach((task, ti) => { for (let k = 0; k < N; k++) {
  const ns = find(task, 'noskill', k), sk = find(task, 'skill', k)
  const skillIsA = (ti + k) % 2 === 0
  pairs.push({ task, k, A: skillIsA ? sk : ns, B: skillIsA ? ns : sk, skillIsA })
} })
const compared = await parallel(pairs.map(pr => () =>
  agent(`You are a senior ${role} judging two designs head-to-head. You do NOT know how either was produced. Judge the DESIGN, not prose or syntax (assume both compile).\nRead the requirements + extension probe: in ${cfg.tasksPath} find id === "${pr.task}"; treat prompts.${variant} as the requirements and "extension" as a future change request.\nRead the rubric principles: ${cfg.rubricPath}\nDesign A: ${cfg.outDir}/blind/${pr.A.id}.md\nDesign B: ${cfg.outDir}/blind/${pr.B.id}.md\nDecide which design a senior engineer would rather OWN, MAINTAIN, and EXTEND (apply the extension probe mentally) — better module boundaries, interface placement & size, dependency direction, zero-value/construction, composition, idiomatic elegance. Be decisive; only tie if truly indistinguishable. Return ONLY:\nWINNER=A|B|TIE\nMARGIN=clear|slight|tie\nREASON=<one line: the deciding architectural difference>`,
    { label: `cmp:${pr.task}:${pr.k}`, phase: 'Compare' })
  .then(text => {
    const w = (/WINNER\s*=\s*(A|B|TIE)/i.exec(text || '') || [])[1]
    let winner = 'tie'
    if (w === 'A') winner = pr.skillIsA ? 'skill' : 'noskill'
    else if (w === 'B') winner = pr.skillIsA ? 'noskill' : 'skill'
    return { task: pr.task, winner, raw: text }
  })))

phase('Signals')
const sigList = (cfg.signals || []).join('\n')
const signalled = await parallel(units.map(u => () =>
  agent(`Count objective architecture signals in this design. Read: ${cfg.outDir}/blind/${u.id}.md\nFor each signal below, output it as NAME=NUMBER (integer or 0-100 percentage; if not applicable use 0). Be literal — count what's actually in the code, not what's implied.\nSignals:\n${sigList}\nReturn ONLY the NAME=NUMBER lines, one per signal.`,
    { label: `sig:${u.task}:${u.cell}:${u.k}`, phase: 'Signals' })
  .then(text => {
    const m = {}
    for (const line of (text || '').split('\n')) {
      const mm = /^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(-?\d+(?:\.\d+)?)/.exec(line)
      if (mm) m[mm[1]] = parseFloat(mm[2])
    }
    return { cell: u.cell, vals: m }
  })))

// aggregate
const tally = { skill: 0, noskill: 0, tie: 0 }
for (const c of compared.filter(Boolean)) tally[c.winner]++
const perTask = {}
for (const task of cfg.taskIds) {
  const rows = compared.filter(c => c && c.task === task)
  perTask[task] = { skill: rows.filter(r => r.winner === 'skill').length, noskill: rows.filter(r => r.winner === 'noskill').length, tie: rows.filter(r => r.winner === 'tie').length }
}
const mean = a => a.length ? +(a.reduce((s, x) => s + x, 0) / a.length).toFixed(2) : null
const signalKeys = [...new Set(signalled.flatMap(s => s ? Object.keys(s.vals) : []))]
const signals = {}
for (const cell of ['noskill', 'skill']) {
  signals[cell] = {}
  const rows = signalled.filter(s => s && s.cell === cell)
  for (const key of signalKeys) signals[cell][key] = mean(rows.map(r => r.vals[key]).filter(x => x != null))
}
log(`winrate skill=${tally.skill} noskill=${tally.noskill} tie=${tally.tie} (of ${compared.length})`)
return { winRate: tally, perTask, signals, nComparisons: compared.length }
