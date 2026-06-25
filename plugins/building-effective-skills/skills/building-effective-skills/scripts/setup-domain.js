// Turnkey domain setup: builds the authority rubric + frozen task prompts in one workflow.
// Invoke: Workflow({ scriptPath: ".../setup-domain.js", args: <config> })
// args arrives JSON-encoded -> JSON.parse.
// config = {
//   outDir:          string,        // writes outDir/RUBRIC.md
//   rubricInstruction:string,       // domain-specific: what to grade, which authority docs, 5 dims + caps
//   taskInstruction: string,        // domain-specific: tasks to define, personas for the naive prompt(s)
//   nTasks:          number,         // expected task count (for the schema)
//   personas:        string[]        // naive-prompt variant names the task-writer must produce, e.g. ["operator","pm","beg"]
// }
// Returns { rubricSummary, tasks } where each task has prompts:{<persona>:..., expert:...}

export const meta = {
  name: 'setup-domain',
  description: 'Build an authority-grounded rubric and persona/expert task prompts for a skill benchmark',
  phases: [{ title: 'Setup' }],
}
const cfg = typeof args === 'string' ? JSON.parse(args) : (args || {})
phase('Setup')

const variantProps = {}
for (const p of (cfg.personas || ['operator'])) variantProps[p] = { type: 'string' }
variantProps.expert = { type: 'string' }

const TASK_SCHEMA = {
  type: 'object', required: ['tasks'],
  properties: { tasks: { type: 'array', minItems: cfg.nTasks || 4, maxItems: cfg.nTasks || 4,
    items: { type: 'object', required: ['id', 'difficulty', 'prompts'],
      properties: {
        id: { type: 'string' }, difficulty: { type: 'string', enum: ['easy', 'hard'] },
        prompts: { type: 'object', required: [...(cfg.personas || ['operator']), 'expert'], properties: variantProps },
      } } } },
}

const personaGuide = `Naive prompt personas (write one prompt per persona, all facts preserved, ZERO technique):\n` +
  `- operator: knows the goal + facts, can't read code, informal, mild hedging ("i think...").\n` +
  `- pm: rushed, terse, business/outcome framing, no technical detail beyond essentials.\n` +
  `- beg: a beginner who states a CONFIDENTLY WRONG technical assumption that a good answer must quietly override.\n` +
  `expert prompt: same task + an inlined expert checklist (the taste to transfer), one-shot, NO file refs, genuinely strong (no strawman).`

const [rubric, tasks] = await parallel([
  () => agent(`${cfg.rubricInstruction}\n\nWrite the rubric to ${cfg.outDir}/RUBRIC.md. Score the DECISION not vocabulary; wrong-but-plausible moves must hit CAPS that override the bands. Return a 6-line summary + a "Sources:" list of exact authority URLs.`,
    { label: 'authority-rubric', phase: 'Setup', effort: 'high' }),
  () => agent(`${cfg.taskInstruction}\n\n${personaGuide}\nProduce exactly ${cfg.nTasks || 4} tasks (mix easy/hard). Return via the schema; each task's prompts object must contain every persona key plus "expert".`,
    { label: 'task-definitions', phase: 'Setup', schema: TASK_SCHEMA }),
])
return { rubricSummary: rubric, tasks: tasks ? tasks.tasks : null }
