---
name: effective-claude
description: Design thinking for building systems with Claude Code. Use when building hooks, daemons, agent pipelines, skills, multi-agent systems, background automations, or any system where Claude Code components connect. Also use when the task involves autonomous agents, scheduled tasks, or any pipeline where LLM output feeds into another system.
---

# Effective Claude -- Building Systems That Work

Synthesized from: Anthropic's "Building Effective Agents" article, AutoAgent (self-improving harnesses), Boris Cherny's workflow, Thariq's "Seeing Like an Agent," production experience running 14-product agencies on Claude, and 5 iterations of the effective-go skill experiment.

**The core finding:** the bottleneck is the harness design, not the model's capability. A well-designed harness with a cheap model outperforms a bad harness with an expensive one.

## Before Building: Three Questions

**1. What question does this system answer for the human?**
Not "what does it do" -- what does the human learn from its output? "Are my servers healthy?" "Is this PR safe?" One sentence. If you can't state it, the system is too vague to build.

**2. Who verifies the output?**
Boris's #1 tip: verification produces 2-3x quality. Options, ranked by cost:
- Deterministic script validates format/content (cheapest, most reliable)
- Self-check: model reviews its own output (cheap, catches obvious errors)
- Cross-model: different model validates (catches subtle errors)
- Human gate: queued for review before acting (safest, slowest)

If nobody verifies, the system will produce garbage and you won't know.

**3. What does failure look like?**
- Halt and report? (good)
- Retry blindly? (expensive)
- Fail silently? (dangerous)
- Generate busywork that looks productive but moves nothing? (hardest to detect)

## Six Design Decisions

### 1. Research -> Plan -> Build (never skip the plan)

Every complex task follows this pipeline with written artifacts:
- **Research:** read deeply, write findings to a file (not verbal)
- **Plan:** write as markdown, iterate 1-6 times with human corrections inline
- **Build:** implementation is mechanical, not creative

The plan is shared mutable state between human and agent. Once approved, the agent executes. If it goes sideways: **revert and re-scope, never incrementally patch a bad approach.**

Skip only for truly trivial tasks (< 3 files, obvious approach).

### 2. Design From the Consumer Backwards

Start at the output, work backwards to the inputs.

The effective-go experiment proved this: V5 (120 lines, focused on blind spots) outperformed V3 (300 lines, comprehensive). Removing dead weight freed attention budget. Same for data pipelines:

| Stage | Compresses to |
|-------|--------------|
| Raw tool calls | Session digest: 3-5 lines (what was asked, what happened, outcome) |
| Session digests | Daily summary: patterns, anomalies, action items |
| Daily summaries | Briefing: 3 bullets for the human |

Each stage removes 80% and keeps the signal. If a downstream model receives >50 lines of structured data, you haven't distilled enough.

### 3. Match Model to Task (and Input Size)

From AutoAgent: same-model meta/task pairings win because the meta-agent writes harnesses the inner model understands.

| Task | Model | Input budget |
|------|-------|-------------|
| Routing, scoring, yes/no | Haiku | <20 lines |
| Code review, implementation | Sonnet | <500 lines of diff |
| Architecture, novel problems | Opus | Worth the cost |
| Format validation | Script (no model) | Free, deterministic |

Haiku with 20 focused lines >> Haiku with 352 raw JSON lines.

### 4. Choose Autonomy Level Deliberately

Two valid extremes exist:
- Agency running 14 products: "human gates every output before publishing"
- AutoAgent: "NEVER STOP. Continue iterating until interrupted"

Both correct for different contexts:

| Level | When | Failure mode to watch |
|-------|------|-----------------------|
| **Fully gated** | Actions visible to others (PR comments, emails, deploys) | Bottleneck on human |
| **Score-gated** | Internal quality improvement (AutoAgent pattern) | Gaming the metric |
| **Circuit-breaker** | Background monitoring | Silent degradation |
| **Fully autonomous** | Sandboxed experiments with measurable outcomes | Expensive flailing |

Default to gated. Earn autonomy with demonstrated reliability. The agency guy's hard-won lesson: "agents create productive-looking work that doesn't move actual business metrics." Busywork is the default failure mode of autonomous agents.

### 5. Halt, Don't Flail

When stuck:
1. Stop immediately (don't retry the same approach)
2. Capture what happened (error, trace, what was attempted)
3. Record the lesson (what went wrong, why, what would fix it)
4. Halt or move on

From AutoAgent: "discarded runs still provide learning signal." A failed experiment with a good trace is more valuable than a succeeded experiment with no trace. **Traces are everything -- without trajectories, improvement rate drops hard.**

The 2-strike rule applies to system design: if a pipeline stage doesn't work after 2 attempts, the design is wrong, not the input.

### 6. Persist Intent, Not Noise

From the agency: "memory persistence is the single biggest unlock."
From AutoAgent: "traces are everything."

These are the same insight: **persist what helps the next run, discard what doesn't.**

| Persist | Why | Example |
|---------|-----|---------|
| User prompts | Intent is the signal | "fix the gateway hook" |
| Session digests | Compressed context | "astrobot: 12 edits, tsc passes" |
| Lessons from failures | Prevent repeats | "model ID must be exact" |
| Scores/outcomes | Track improvement | "review quality: 7/10" |

Do NOT persist: raw tool call logs, full LLM outputs, intermediate state.

## Hard Rules (things to DO, not consider)

**Complexity matching:** If the system's main job is calling `claude -p` and processing the output, write it in bash. Only use Go/Python when there's real logic -- concurrency, data structures, HTTP servers. A 50-line shell script beats a 500-line Go binary that just shells out.

**Every external action gets --dry-run.** If the system posts PR comments, sends emails, deploys code, or modifies remote state: it MUST have a `--dry-run` flag that shows what it WOULD do without doing it. This is non-negotiable for testing and trust.

**Verification is not optional.** After the system produces output, something must check it:
- Script that validates format/content (cheapest)
- `| head -20` review of what would be posted (minimum viable)
- Self-review: "rate this output 1-10" haiku call (cheap)
Build the verification BEFORE the action, not after you discover the output is garbage.

**Circuit breaker for anything that loops.** Any daemon, cron job, or recurring task needs: max failures before halt, cooldown period, and a log of why it stopped. Without this, a $0.01/run task at 3am becomes a $50 bill by morning.

**Cost per run, always.** Every system that calls `claude -p` must log token count and estimated cost per invocation. Not as a nice-to-have -- as a core output alongside the result.

**Subagents get the FULL brief.** When spawning a teammate or subagent, pass the complete context: design direction, constraints, existing patterns, what NOT to do. Subagents can't see your conversation. If you summarize to save tokens, the subagent will produce scaffolding that ignores the user's actual intent. The cost of a longer prompt is always less than the cost of rebuilding garbage output.

**Revert, don't patch.** When a subagent or previous approach produced wrong output, delete it and rebuild with the right direction. Don't "assess the damage" and incrementally fix -- that preserves the wrong architecture. The sunk cost is already sunk. `git checkout -- .` is cheaper than 10 rounds of fixes.

**Never suggest stopping.** Don't offer "good stopping points" or ask "want to pick this up later?" The human's cost of re-establishing context is always higher than your cost of continuing. Complex infra work (cloud deployments, multi-service migrations, fleet operations) can't be paused and resumed cheaply. Let the human decide when to stop. Just keep working.

## Execution Environment

- `claude -p` hangs on questions -- always use `--max-turns`
- Model IDs exact: `claude-haiku-4-5`, `claude-sonnet-4-6`, `claude-opus-4-6`
- Async hooks have no terminal -- `tty` fails
- Systemd: no shell profile -- set PATH/HOME explicitly
- Hook exit codes: 0=success, 2=block
- Skill frontmatter loads into EVERY session -- keep it short
- PostCompact hook: re-inject critical instructions after compression
- Bash wrapping `claude -p` almost always beats a compiled binary doing the same
