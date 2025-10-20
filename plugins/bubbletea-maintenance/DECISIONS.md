# Architecture Decisions

Documentation of key design decisions for Bubble Tea Maintenance Agent.

## Core Purpose Decision

**Decision**: Focus on maintenance/debugging of existing Bubble Tea apps, not design

**Rationale**:
- ✅ Complements `bubbletea-designer` agent (design) with maintenance agent (upkeep)
- ✅ Different problem space: diagnosis vs creation
- ✅ Users have existing apps that need optimization
- ✅ Maintenance is ongoing, design is one-time

**Alternatives Considered**:
- Combined design+maintenance agent: Too broad, conflicting concerns
- Generic Go linter: Misses Bubble Tea-specific patterns

---

## Data Source Decision

**Decision**: Use local tip-bubbltea-apps.md file as knowledge base

**Rationale**:
- ✅ No internet required (offline capability)
- ✅ Fast access (local file system)
- ✅ Expert-curated knowledge (leg100.github.io)
- ✅ 11 specific, actionable tips
- ✅ Can be updated independently

**Alternatives Considered**:
- Web scraping: Fragile, requires internet, slow
- Embedded knowledge: Hard to update, limited
- API: Rate limits, auth, network dependency

**Trade-offs**:
- User needs to have tip file locally
- Updates require manual file replacement

---

## Analysis Approach Decision

**Decision**: 6 separate specialized functions + 1 orchestrator

**Rationale**:
- ✅ Single Responsibility Principle
- ✅ Composable - can use individually or together
- ✅ Testable - each function independently tested
- ✅ Flexible - run quick diagnosis or deep analysis

**Structure**:
1. `diagnose_issue()` - General problem identification
2. `apply_best_practices()` - Validate against 11 tips
3. `debug_performance()` - Performance bottleneck detection
4. `suggest_architecture()` - Refactoring recommendations
5. `fix_layout_issues()` - Lipgloss layout fixes
6. `comprehensive_analysis()` - Orchestrates all 5

**Alternatives Considered**:
- Single monolithic function: Hard to test, maintain, customize
- 20 micro-functions: Too granular, confusing
- Plugin architecture: Over-engineered for v1.0

---

## Code Parsing Strategy

**Decision**: Regex-based parsing instead of AST

**Rationale**:
- ✅ Fast - no parse tree construction
- ✅ Simple - easy to understand, maintain
- ✅ Good enough - catches 90% of issues
- ✅ No external dependencies (go/parser)
- ✅ Cross-platform - pure Python

**Alternatives Considered**:
- AST parsing (go/parser): More accurate but slow, complex
- Token-based: Middle ground, still complex
- LLM-based: Overkill, slow, requires API

**Trade-offs**:
- May miss edge cases (rare nested structures)
- Can't detect all semantic issues
- Good for pattern matching, not deep analysis

**When to upgrade to AST**:
- v2.0 if accuracy becomes critical
- If false positive rate >5%
- If complex refactoring automation is added

---

## Validation Strategy

**Decision**: Multi-layer validation with severity levels

**Rationale**:
- ✅ Early error detection
- ✅ Clear prioritization (CRITICAL > WARNING > INFO)
- ✅ Actionable feedback
- ✅ User can triage fixes

**Severity Levels**:
- **CRITICAL**: Breaks UI, must fix immediately
- **HIGH**: Significant performance/reliability impact
- **MEDIUM**: Noticeable but not critical
- **WARNING**: Best practice violation
- **LOW**: Minor optimization
- **INFO**: Suggestions, not problems

**Validation Layers**:
1. Input validation (paths exist, files readable)
2. Structure validation (result format correct)
3. Content validation (scores in range, fields present)
4. Semantic validation (recommendations make sense)

---

## Performance Threshold Decision

**Decision**: Update() <16ms, View() <3ms targets

**Rationale**:
- 16ms = 60 FPS (1000ms / 60 = 16.67ms)
- View() should be faster (called more often)
- Based on Bubble Tea best practices
- Leaves budget for framework overhead

**Measurement**:
- Static analysis (pattern detection, not timing)
- Identifies blocking operations
- Estimates based on operation type:
  - HTTP request: 50-200ms
  - File I/O: 1-100ms
  - Regex compile: 1-10ms
  - String concat: 0.1-1ms per operation

**Future**: v2.0 could integrate pprof for actual measurements

---

## Architecture Pattern Decision

**Decision**: Heuristic-based pattern detection and recommendations

**Rationale**:
- ✅ Works without user input
- ✅ Based on complexity metrics
- ✅ Provides concrete steps
- ✅ Includes code templates

**Complexity Scoring** (0-100):
- File count (10 points max)
- Model field count (20 points)
- Update() case count (20 points)
- View() line count (15 points)
- Custom message count (10 points)
- View function count (15 points)
- Concurrency usage (10 points)

**Pattern Recommendations**:
- <30: flat_model (simple)
- 30-70: multi_view or component_based (medium)
- 70+: model_tree (complex)

---

## Best Practices Integration

**Decision**: Map each of 11 tips to automated checks

**Rationale**:
- ✅ Leverages expert knowledge
- ✅ Specific, actionable tips
- ✅ Comprehensive coverage
- ✅ Education + validation

**Tip Mapping**:
1. Fast event loop → Check for blocking ops in Update()
2. Debug dumping → Look for spew/io.Writer
3. Live reload → Check for air config
4. Receiver methods → Validate Update() receiver type
5. Message ordering → Check for state tracking
6. Model tree → Analyze model complexity
7. Layout arithmetic → Validate lipgloss.Height() usage
8. Terminal recovery → Check for defer/recover
9. teatest → Look for test files
10. VHS → Check for .tape files
11. Resources → Info-only

---

## Error Handling Strategy

**Decision**: Return errors in result dict, never raise exceptions

**Rationale**:
- ✅ Graceful degradation
- ✅ Partial results still useful
- ✅ Easy to aggregate errors
- ✅ Doesn't break orchestrator

**Format**:
```python
{
    "error": "Description",
    "validation": {
        "status": "error",
        "summary": "What went wrong"
    }
}
```

**Philosophy**:
- Better to return partial analysis than fail completely
- User can act on what was found
- Errors are just another data point

---

## Report Format Decision

**Decision**: JSON output with CLI-friendly summary

**Rationale**:
- ✅ Machine-readable (JSON for tools)
- ✅ Human-readable (CLI summary)
- ✅ Composable (can pipe to jq, etc.)
- ✅ Saveable (file output)

**Structure**:
```python
{
    "overall_health": 75,
    "sections": {
        "issues": {...},
        "best_practices": {...},
        "performance": {...},
        "architecture": {...},
        "layout": {...}
    },
    "priority_fixes": [...],
    "summary": "Executive summary",
    "estimated_fix_time": "2-4 hours",
    "validation": {...}
}
```

---

## Testing Strategy

**Decision**: Unit tests per function + integration tests

**Rationale**:
- ✅ Each function independently tested
- ✅ Integration tests verify orchestration
- ✅ Test fixtures for common scenarios
- ✅ ~90% code coverage target

**Test Structure**:
```
tests/
├── test_diagnose_issue.py       # diagnose_issue() tests
├── test_best_practices.py       # apply_best_practices() tests
├── test_performance.py          # debug_performance() tests
├── test_architecture.py         # suggest_architecture() tests
├── test_layout.py               # fix_layout_issues() tests
└── test_integration.py          # End-to-end tests
```

**Test Coverage**:
- Happy path (valid code)
- Edge cases (empty files, no functions)
- Error cases (invalid paths, bad Go code)
- Integration (orchestrator combines correctly)

---

## Documentation Strategy

**Decision**: Comprehensive SKILL.md + reference docs

**Rationale**:
- ✅ Self-contained (agent doesn't need external docs)
- ✅ Examples for every pattern
- ✅ Education + automation
- ✅ Quick reference guides

**Documentation Files**:
1. **SKILL.md** - Complete agent instructions (8,000 words)
2. **README.md** - Quick start guide
3. **common_issues.md** - Problem/solution catalog
4. **CHANGELOG.md** - Version history
5. **DECISIONS.md** - This file
6. **INSTALLATION.md** - Setup guide

---

## Future Enhancements

**v2.0 Ideas**:
- AST-based parsing for higher accuracy
- Integration with pprof for actual profiling data
- Automated fix application (not just suggestions)
- Custom rule definitions
- Visual reports
- CI/CD integration
- GitHub Action for PR checks
- VSCode extension integration

**Criteria for v2.0**:
- User feedback indicates accuracy issues
- False positive rate >5%
- Users request automated fixes
- Adoption reaches 100+ users

---

**Built with Claude Code agent-creator on 2025-10-19**
