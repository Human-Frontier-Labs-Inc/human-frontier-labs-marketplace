# Benchmark Results

Two controlled experiments using Claude Code peers building real apps side-by-side.

## Setup

Two Claude Code sessions running simultaneously on the same machine. Peer A has the effective-go skill loaded. Peer B does not. Both build the same apps from the same prompts. All analysis is deterministic (`go build`, `go vet`, grep-based anti-pattern detection, interface counting).

## Experiment 1: Same Vague Prompt, Skill vs No Skill

**App:** Service health checker
**Prompt (identical to both):** "go thing that checks if a bunch of services are up -- pings urls and ports on a schedule, shows status in terminal, alerts when something goes down. save state so I can see history"

| Metric | WITH skill | WITHOUT skill |
|--------|-----------|--------------|
| Compiles | Yes | Yes |
| Vet clean | Yes | Yes |
| **Interfaces** | **3** (Checker:1m, ConfigStore:2m, HistoryStore:2m) | **0** |
| **Embedding** | **Yes** | No |
| **Typed constants** | **4** | 1 |
| Lines | 1314 | 1047 |
| Files | 7 | 6 |

Same prompt, completely different architecture. The skill version defines 3 small, consumer-side interfaces and uses struct embedding. The baseline version has none.

## Experiment 2: Skill + Vague Prompt vs No Skill + Detailed Spec

**App:** Expense tracker CLI
**The question:** Can a non-coder with the skill produce better Go architecture than a developer writing a detailed spec without it?

**Peer A prompt (vague, non-coder):**
> "make me a terminal expense tracker -- add expenses with categories and amounts, show monthly summaries, export to csv. save to a file between runs"

**Peer B prompt (detailed CS-dev spec):**
> "Build a CLI expense tracker in Go using cobra for commands. Support these subcommands: add (amount, category, description, date), list (with filters by category/date range/amount), summary (monthly aggregation with category breakdown), export (CSV output to stdout or file). Store data in a JSON file in ~/.config/expenses/data.json. Define an Expense struct with proper types (time.Time for dates, float64 for amounts). Create a Storage interface for the data layer so it's testable. Use lipgloss for colored terminal output."

| Metric | Skill + vague prompt | No skill + detailed spec |
|--------|---------------------|------------------------|
| Compiles | Yes | Yes |
| **Vet clean** | **Yes** | **No** |
| **Interfaces** | **2** (ExpenseStore:2m, Exporter:1m) | 1 (Storage:4m) |
| **Typed constants** | **4** | **0** |
| Lines | 1129 | 660 |
| Files | 7 | 8 |

**The non-coder with the skill produced better architecture than the detailed spec without it.**

- The skill version has 2 narrow interfaces (1-2 methods each). The spec version has 1 fat 4-method interface -- even though the spec explicitly asked for "a Storage interface."
- The skill version has 4 typed constants. The spec version has 0 -- raw strings for categories despite the developer knowing better.
- The spec version doesn't even pass `go vet`. The vague prompt version does.

## What This Means

The skill embeds senior Go engineer taste directly into the model. A non-coder typing "make me a thing" gets the same architectural quality -- small interfaces, typed constants, proper composition -- that an experienced developer would produce. The skill compensates for missing domain knowledge in the prompt.

Raw analysis data in `benchmarks/raw/`.
