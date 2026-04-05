# effective-go

Claude Code plugin that makes Claude write architecturally tasteful Go -- not just code that compiles, but code a senior Go developer would approve of.

## Install

```bash
claude plugin marketplace add https://github.com/williavs/effective-go-plugin
claude plugin install effective-go
```

Or manually:
```bash
git clone https://github.com/williavs/effective-go-plugin ~/.claude/plugins/effective-go
```

## The Problem

Claude writes Go that compiles and runs but reads like translated Java. The syntax is fine -- formatting, naming, error handling all work. What's missing is architectural taste: zero-value types, small consumer-defined interfaces, composition via embedding, typed constants instead of raw strings.

## What the Skill Teaches

Five things Claude doesn't naturally do in Go:

1. **Zero-value design** -- make `var x T` usable without a constructor
2. **Consumer-defined interfaces** -- 1-2 method interfaces defined where they're used, not where they're implemented
3. **Composition via embedding** -- promote methods instead of wrapping them
4. **Typed constants** -- named types for closed value sets, never raw strings
5. **Standard library first** -- `sort.Slice`, not hand-rolled loops

## Results

We tested by running two Claude Code sessions side-by-side building the same apps. One had the skill, one didn't.

**Headline finding:** A non-coder typing a vague prompt with the skill produces better Go architecture than a detailed CS-dev spec without it.

| | Skill + vague prompt | No skill + detailed spec |
|--|---------------------|------------------------|
| Interfaces | 2 small (1-2 methods) | 1 fat (4 methods) |
| Typed constants | 4 | 0 |
| `go vet` clean | Yes | No |

The skill embeds senior engineer taste into every Go request, regardless of who's prompting.

See [benchmarks/BENCHMARK.md](benchmarks/BENCHMARK.md) for full methodology and data.

## How We Got Here

This skill went through 5 iterations of testing:

1. **V1 -- Pattern checklist** (300 lines). Listed every Effective Go rule. Marginal improvement -- Claude already knows Go syntax.
2. **V2 -- Design thinking** (280 lines). Taught the thinking process before coding. First time interfaces and zero-value design appeared in outputs.
3. **V3 -- Hard rules added** (300 lines). 8 concrete rules from deep code review of V2 outputs (`no os.Exit outside main`, `no hand-rolled sorts`, etc.).
4. **V4 -- Anti-paralysis fix** (290 lines). V3 caused "planning paralysis" on vague prompts -- too much design thinking, not enough coding. Fixed the framing.
5. **V5 -- Lean** (120 lines). Removed everything Claude already does well. Kept only the 5 blind spots. The biggest improvement came from **cutting the skill in half**. Confirmed by Anthropic's own guidance: "every token added depletes Claude's attention budget."

Each iteration was tested with deterministic analysis: compilation, `go vet`, grep-based anti-pattern detection, interface counting. No LLM grading.

## What's Included

| Component | Description |
|-----------|-------------|
| `skills/effective-go/SKILL.md` | The skill (auto-triggers on Go code) |
| `skills/effective-go/references/` | Full Effective Go pattern reference |
| `skills/effective-go/scripts/analyze.sh` | Deterministic Go code analyzer (JSON output) |
| `agents/go-reviewer.md` | On-demand code review agent |
| `benchmarks/` | Raw experiment data |

## License

MIT
