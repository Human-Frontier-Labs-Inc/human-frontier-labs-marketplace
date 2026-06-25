// Multi-turn DRIFT benchmark — the authentic test of a non-expert building over time.
// A non-expert drives a build across several turns; the model extends the SAME codebase each turn.
// Two arms: with-skill vs no-skill. After N turns, compare the resulting codebases pairwise
// (which would a senior dev rather inherit) + drift signals. args arrives JSON-encoded -> JSON.parse.
//
// config = {
//   outDir, skillPath, rubricPath, what (e.g. "Bubble Tea terminal task app"),
//   role, turns: ["non-expert feature request", ...], chains (independent builds per arm),
//   genModel (optional), signals: [ "name: how to count, good dir", ... ]
// }
// Returns { winRate, perChain, signals:{arm:{name:mean}}, turns:N }

export const meta = {
  name: 'run-multiturn',
  description: 'Multi-turn drift benchmark: non-expert builds over turns, skill vs no-skill, pairwise + drift signals',
  phases: [{ title: 'Build' }, { title: 'Compare' }, { title: 'Signals' }],
}
const cfg = typeof args === 'string' ? JSON.parse(args) : (args || {})
const TURNS = cfg.turns
const CHAINS = cfg.chains || 3
const role = cfg.role || 'engineer'

phase('Build')
const buildChain = (c, arm) => async () => {
  let prev = null
  for (let t = 0; t < TURNS.length; t++) {
    const out = `${cfg.outDir}/c${c}_${arm}/turn${t}.md`
    const ctx = prev
      ? `The current codebase so far is in the file ${prev} — READ it first and CONTINUE the SAME project, keeping all prior features working. Do not restart from scratch.`
      : `This is the first step — start the project.`
    const skillLine = arm === 'skill'
      ? `FIRST read and apply this skill in full: ${cfg.skillPath}. `
      : `Answer from your own knowledge ONLY; do not read or use any skill/plugin/reference file other than the codebase file named below; do not use the Skill tool. `
    const p = `${skillLine}You are helping a non-expert who cannot read code well build a ${cfg.what} in Go, over several steps. ${ctx}\nThe user now says: "${TURNS[t]}"\nWrite the COMPLETE updated codebase (every file, full contents, with filenames as headers) to: ${out}\nReturn only "done".`
    const opts = { label: `build:c${c}:${arm}:t${t}`, phase: 'Build' }
    if (cfg.genModel) opts.model = cfg.genModel
    await agent(p, opts)
    prev = out
  }
  return { c, arm, final: prev }
}
const cells = []
for (let c = 0; c < CHAINS; c++) for (const arm of ['noskill', 'skill']) cells.push({ c, arm })
const built = await parallel(cells.map(x => buildChain(x.c, x.arm)))
const finalOf = (c, arm) => (built.find(b => b && b.c === c && b.arm === arm) || {}).final

phase('Compare')
const cmp = await parallel(Array.from({ length: CHAINS }, (_, c) => () => {
  const sk = finalOf(c, 'skill'), ns = finalOf(c, 'noskill')
  if (!sk || !ns) return Promise.resolve(null)
  const skillIsA = c % 2 === 0
  return agent(`You are a senior ${role} inheriting a codebase someone built over several iterations. Judge the DESIGN/taste, not syntax (assume both compile). Which would you rather OWN, MAINTAIN, and keep EXTENDING?\nConsider: clear separation (model/update/view, not a god-blob), consistent naming, named message/state types (not stringly-typed), small focused functions, no copy-paste drift, idiomatic structure as it grew.\nRubric principles: ${cfg.rubricPath}\nCodebase A: ${skillIsA ? sk : ns}\nCodebase B: ${skillIsA ? ns : sk}\nReturn ONLY:\nWINNER=A|B|TIE\nMARGIN=clear|slight|tie\nREASON=<one line: the deciding difference in maintainability/taste>`,
    { label: `cmp:c${c}`, phase: 'Compare' })
    .then(text => {
      const w = (/WINNER\s*=\s*(A|B|TIE)/i.exec(text || '') || [])[1]
      let winner = 'tie'
      if (w === 'A') winner = skillIsA ? 'skill' : 'noskill'
      else if (w === 'B') winner = skillIsA ? 'noskill' : 'skill'
      return { c, winner, raw: text }
    })
}))

phase('Signals')
const sigList = (cfg.signals || []).join('\n')
const sig = await parallel(cells.map(x => () => {
  const f = finalOf(x.c, x.arm)
  if (!f) return Promise.resolve(null)
  return agent(`Count objective code-quality signals in this final codebase. Read: ${f}\nFor each signal output NAME=NUMBER (integer or 0-100). Count what's actually there.\nSignals:\n${sigList}\nReturn ONLY the NAME=NUMBER lines.`,
    { label: `sig:c${x.c}:${x.arm}`, phase: 'Signals' })
    .then(text => {
      const m = {}
      for (const line of (text || '').split('\n')) { const mm = /^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(-?\d+(?:\.\d+)?)/.exec(line); if (mm) m[mm[1]] = parseFloat(mm[2]) }
      return { arm: x.arm, vals: m }
    })
}))

const tally = { skill: 0, noskill: 0, tie: 0 }
for (const r of cmp.filter(Boolean)) tally[r.winner]++
const mean = a => a.length ? +(a.reduce((s, x) => s + x, 0) / a.length).toFixed(2) : null
const keys = [...new Set(sig.flatMap(s => s ? Object.keys(s.vals) : []))]
const signals = {}
for (const arm of ['noskill', 'skill']) { signals[arm] = {}; const rows = sig.filter(s => s && s.arm === arm); for (const k of keys) signals[arm][k] = mean(rows.map(r => r.vals[k]).filter(x => x != null)) }
log(`drift winrate skill=${tally.skill} noskill=${tally.noskill} tie=${tally.tie}`)
return { winRate: tally, perChain: cmp.filter(Boolean), signals, turns: TURNS.length, chains: CHAINS }
