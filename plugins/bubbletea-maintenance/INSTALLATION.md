# Installation Guide

Step-by-step guide to installing and using the Bubble Tea Maintenance Agent.

---

## Prerequisites

**Required:**
- Python 3.8+
- Claude Code CLI installed

**Optional (for full functionality):**
- `/Users/williamvansickleiii/charmtuitemplate/charm-tui-template/tip-bubbltea-apps.md`
- `/Users/williamvansickleiii/charmtuitemplate/charm-tui-template/lipgloss-readme.md`

---

## Installation Steps

### 1. Navigate to Agent Directory

```bash
cd /Users/williamvansickleiii/charmtuitemplate/vinw/bubbletea-designer/bubbletea-maintenance
```

### 2. Verify Files

Check that all required files exist:

```bash
ls -la
```

You should see:
- `.claude-plugin/marketplace.json`
- `SKILL.md`
- `README.md`
- `scripts/` directory
- `references/` directory
- `tests/` directory

### 3. Install the Agent

```bash
/plugin marketplace add .
```

Or from within Claude Code:

```
/plugin marketplace add /Users/williamvansickleiii/charmtuitemplate/vinw/bubbletea-designer/bubbletea-maintenance
```

### 4. Verify Installation

The agent should now appear in your Claude Code plugins list:

```
/plugin list
```

Look for: `bubbletea-maintenance`

---

## Testing the Installation

### Quick Test

Ask Claude Code:

```
"Analyze my Bubble Tea app at /path/to/your/app"
```

The agent should activate and run a comprehensive analysis.

### Detailed Test

Run the test suite:

```bash
cd /Users/williamvansickleiii/charmtuitemplate/vinw/bubbletea-designer/bubbletea-maintenance
python3 -m pytest tests/ -v
```

Expected output:
```
tests/test_diagnose_issue.py ✓✓✓✓
tests/test_best_practices.py ✓✓✓✓
tests/test_performance.py ✓✓✓✓
tests/test_architecture.py ✓✓✓✓
tests/test_layout.py ✓✓✓✓
tests/test_integration.py ✓✓✓

======================== XX passed in X.XXs ========================
```

---

## Configuration

### Setting Up Local References

For full best practices validation, ensure these files exist:

1. **tip-bubbltea-apps.md**
   ```bash
   ls /Users/williamvansickleiii/charmtuitemplate/charm-tui-template/tip-bubbltea-apps.md
   ```

   If missing, the agent will still work but best practices validation will be limited.

2. **lipgloss-readme.md**
   ```bash
   ls /Users/williamvansickleiii/charmtuitemplate/charm-tui-template/lipgloss-readme.md
   ```

### Customizing Paths

If your reference files are in different locations, update paths in:
- `scripts/apply_best_practices.py` (line 16: `TIPS_FILE`)

---

## Usage Examples

### Example 1: Diagnose Issues

```
User: "My Bubble Tea app is slow, diagnose issues"

Agent: [Runs diagnose_issue()]
Found 3 issues:
1. CRITICAL: Blocking HTTP request in Update() (main.go:45)
2. WARNING: Hardcoded terminal width (main.go:89)
3. INFO: Consider model tree pattern for 18 fields

[Provides fixes for each]
```

### Example 2: Check Best Practices

```
User: "Check if my TUI follows best practices"

Agent: [Runs apply_best_practices()]
Overall Score: 75/100

✅ PASS: Fast event loop
✅ PASS: Terminal recovery
⚠️  FAIL: No debug message dumping
⚠️  FAIL: No tests with teatest
INFO: No VHS demos (optional)

[Provides recommendations]
```

### Example 3: Comprehensive Analysis

```
User: "Run full analysis on ./myapp"

Agent: [Runs comprehensive_bubbletea_analysis()]

=================================================================
COMPREHENSIVE BUBBLE TEA ANALYSIS
=================================================================

Overall Health: 78/100
Summary: Good health. Some improvements recommended.

Priority Fixes (5):

🔴 CRITICAL (1):
  1. [Performance] Blocking HTTP request in Update() (main.go:45)

⚠️  WARNINGS (2):
  2. [Best Practices] Missing debug message dumping
  3. [Layout] Hardcoded dimensions in View()

💡 INFO (2):
  4. [Architecture] Consider model tree pattern
  5. [Performance] Cache lipgloss styles

Estimated Fix Time: 2-4 hours

Full report saved to: ./bubbletea_analysis_report.json
```

---

## Troubleshooting

### Issue: Agent Not Activating

**Solution 1: Check Installation**
```bash
/plugin list
```

If not listed, reinstall:
```bash
/plugin marketplace add /path/to/bubbletea-maintenance
```

**Solution 2: Use Explicit Activation**

Instead of:
```
"Analyze my Bubble Tea app"
```

Try:
```
"Use the bubbletea-maintenance agent to analyze my app"
```

### Issue: "No .go files found"

**Cause**: Wrong path provided

**Solution**: Use absolute path or verify path exists:
```bash
ls /path/to/your/app
```

### Issue: "tip-bubbltea-apps.md not found"

**Impact**: Best practices validation will be limited

**Solutions**:

1. **Get the file**:
   ```bash
   # If you have charm-tui-template
   ls /Users/williamvansickleiii/charmtuitemplate/charm-tui-template/tip-bubbltea-apps.md
   ```

2. **Update path** in `scripts/apply_best_practices.py`:
   ```python
   TIPS_FILE = Path("/your/custom/path/tip-bubbltea-apps.md")
   ```

3. **Or skip best practices**:
   The other 5 functions still work without it.

### Issue: Tests Failing

**Check Python Version**:
```bash
python3 --version  # Should be 3.8+
```

**Install Test Dependencies**:
```bash
pip3 install pytest
```

**Run Individual Tests**:
```bash
python3 tests/test_diagnose_issue.py
```

### Issue: Permission Denied

**Solution**: Make scripts executable:
```bash
chmod +x scripts/*.py
```

---

## Uninstallation

To remove the agent:

```bash
/plugin marketplace remove bubbletea-maintenance
```

Or manually delete the plugin directory:
```bash
rm -rf /path/to/bubbletea-maintenance
```

---

## Upgrading

### To v1.0.1+

1. **Backup your config** (if you customized paths)
2. **Remove old version**:
   ```bash
   /plugin marketplace remove bubbletea-maintenance
   ```
3. **Install new version**:
   ```bash
   cd /path/to/new/bubbletea-maintenance
   /plugin marketplace add .
   ```
4. **Verify**:
   ```bash
   cat VERSION  # Should show new version
   ```

---

## Support

**Issues**: Check SKILL.md for detailed documentation

**Questions**:
- Read `references/common_issues.md` for solutions
- Check CHANGELOG.md for known limitations

---

## Next Steps

After installation:

1. **Try it out**: Analyze one of your Bubble Tea apps
2. **Read documentation**: Check references/ for guides
3. **Run tests**: Ensure everything works
4. **Customize**: Update paths if needed

---

**Built with Claude Code agent-creator on 2025-10-19**
