# Common Bubble Tea Issues and Solutions

Reference guide for diagnosing and fixing common problems in Bubble Tea applications.

## Performance Issues

### Issue: Slow/Laggy UI

**Symptoms:**
- UI freezes when typing
- Delayed response to key presses
- Stuttering animations

**Common Causes:**

1. **Blocking Operations in Update()**
   ```go
   // ❌ BAD
   func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
       switch msg := msg.(type) {
       case tea.KeyMsg:
           data := http.Get("https://api.example.com")  // BLOCKS!
           m.data = data
       }
       return m, nil
   }

   // ✅ GOOD
   func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
       switch msg := msg.(type) {
       case tea.KeyMsg:
           return m, fetchDataCmd  // Non-blocking
       case dataFetchedMsg:
           m.data = msg.data
       }
       return m, nil
   }

   func fetchDataCmd() tea.Msg {
       data := http.Get("https://api.example.com")  // Runs in goroutine
       return dataFetchedMsg{data: data}
   }
   ```

2. **Heavy Processing in View()**
   ```go
   // ❌ BAD
   func (m model) View() string {
       content, _ := os.ReadFile("large_file.txt")  // EVERY RENDER!
       return string(content)
   }

   // ✅ GOOD
   type model struct {
       cachedContent string
   }

   func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
       switch msg := msg.(type) {
       case fileLoadedMsg:
           m.cachedContent = msg.content  // Cache it
       }
       return m, nil
   }

   func (m model) View() string {
       return m.cachedContent  // Just return cached data
   }
   ```

3. **String Concatenation with +**
   ```go
   // ❌ BAD - Allocates many temp strings
   func (m model) View() string {
       s := ""
       for _, line := range m.lines {
           s += line + "\\n"  // Expensive!
       }
       return s
   }

   // ✅ GOOD - Single allocation
   func (m model) View() string {
       var b strings.Builder
       for _, line := range m.lines {
           b.WriteString(line)
           b.WriteString("\\n")
       }
       return b.String()
   }
   ```

**Performance Target:** Update() should complete in <16ms (60 FPS)

---

## Layout Issues

### Issue: Content Overflows Terminal

**Symptoms:**
- Text wraps unexpectedly
- Content gets clipped
- Layout breaks on different terminal sizes

**Common Causes:**

1. **Hardcoded Dimensions**
   ```go
   // ❌ BAD
   content := lipgloss.NewStyle().
       Width(80).   // What if terminal is 120 wide?
       Height(24).  // What if terminal is 40 tall?
       Render(text)

   // ✅ GOOD
   type model struct {
       termWidth  int
       termHeight int
   }

   func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
       switch msg := msg.(type) {
       case tea.WindowSizeMsg:
           m.termWidth = msg.Width
           m.termHeight = msg.Height
       }
       return m, nil
   }

   func (m model) View() string {
       content := lipgloss.NewStyle().
           Width(m.termWidth).
           Height(m.termHeight - 2).  // Leave room for status bar
           Render(text)
       return content
   }
   ```

2. **Not Accounting for Padding/Borders**
   ```go
   // ❌ BAD
   style := lipgloss.NewStyle().
       Padding(2).
       Border(lipgloss.RoundedBorder()).
       Width(80)
   content := style.Render(text)
   // Text area is 76 (80 - 2*2 padding), NOT 80!

   // ✅ GOOD
   style := lipgloss.NewStyle().
       Padding(2).
       Border(lipgloss.RoundedBorder())

   contentWidth := 80 - style.GetHorizontalPadding() - style.GetHorizontalBorderSize()
   innerContent := lipgloss.NewStyle().Width(contentWidth).Render(text)
   result := style.Width(80).Render(innerContent)
   ```

3. **Manual Height Calculations**
   ```go
   // ❌ BAD - Magic numbers
   availableHeight := 24 - 3  // Where did 3 come from?

   // ✅ GOOD - Calculated
   headerHeight := lipgloss.Height(m.renderHeader())
   footerHeight := lipgloss.Height(m.renderFooter())
   availableHeight := m.termHeight - headerHeight - footerHeight
   ```

---

## Message Handling Issues

### Issue: Messages Arrive Out of Order

**Symptoms:**
- State becomes inconsistent
- Operations complete in wrong order
- Race conditions

**Cause:** Concurrent tea.Cmd messages aren't guaranteed to arrive in order

**Solution: Use State Tracking**

```go
// ❌ BAD - Assumes order
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyMsg:
        if msg.String() == "r" {
            return m, tea.Batch(
                fetchUsersCmd,    // Might complete second
                fetchPostsCmd,    // Might complete first
            )
        }
    case usersLoadedMsg:
        m.users = msg.users
    case postsLoadedMsg:
        m.posts = msg.posts
        // Assumes users are loaded! May not be!
    }
    return m, nil
}

// ✅ GOOD - Track operations
type model struct {
    operations map[string]bool
    users      []User
    posts      []Post
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyMsg:
        if msg.String() == "r" {
            m.operations["users"] = true
            m.operations["posts"] = true
            return m, tea.Batch(fetchUsersCmd, fetchPostsCmd)
        }
    case usersLoadedMsg:
        m.users = msg.users
        delete(m.operations, "users")
        return m, m.checkAllLoaded()
    case postsLoadedMsg:
        m.posts = msg.posts
        delete(m.operations, "posts")
        return m, m.checkAllLoaded()
    }
    return m, nil
}

func (m model) checkAllLoaded() tea.Cmd {
    if len(m.operations) == 0 {
        // All operations complete, can proceed
        return m.processData
    }
    return nil
}
```

---

## Terminal Recovery Issues

### Issue: Terminal Gets Messed Up After Crash

**Symptoms:**
- Cursor disappears
- Mouse mode still active
- Terminal looks corrupted

**Solution: Add Panic Recovery**

```go
func main() {
    defer func() {
        if r := recover(); r != nil {
            // Restore terminal state
            tea.DisableMouseAllMotion()
            tea.ShowCursor()
            fmt.Printf("Panic: %v\\n", r)
            debug.PrintStack()
            os.Exit(1)
        }
    }()

    p := tea.NewProgram(initialModel())
    if err := p.Start(); err != nil {
        fmt.Printf("Error: %v\\n", err)
        os.Exit(1)
    }
}
```

---

## Architecture Issues

### Issue: Model Too Complex

**Symptoms:**
- Model struct has 20+ fields
- Update() is hundreds of lines
- Hard to maintain

**Solution: Use Model Tree Pattern**

```go
// ❌ BAD - Flat model
type model struct {
    // List view fields
    listItems   []string
    listCursor  int
    listFilter  string

    // Detail view fields
    detailItem  string
    detailHTML  string
    detailScroll int

    // Search view fields
    searchQuery string
    searchResults []string
    searchCursor int

    // ... 15 more fields
}

// ✅ GOOD - Model tree
type appModel struct {
    activeView int
    listView   listViewModel
    detailView detailViewModel
    searchView searchViewModel
}

type listViewModel struct {
    items   []string
    cursor  int
    filter  string
}

func (m listViewModel) Update(msg tea.Msg) (listViewModel, tea.Cmd) {
    // Only handles list-specific messages
    switch msg := msg.(type) {
    case tea.KeyMsg:
        switch msg.String() {
        case "up":
            m.cursor--
        case "down":
            m.cursor++
        case "enter":
            return m, func() tea.Msg {
                return itemSelectedMsg{itemID: m.items[m.cursor]}
            }
        }
    }
    return m, nil
}

// Parent routes messages
func (m appModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    // Handle global messages
    switch msg := msg.(type) {
    case itemSelectedMsg:
        m.detailView.LoadItem(msg.itemID)
        m.activeView = 1  // Switch to detail
        return m, nil
    }

    // Route to active child
    var cmd tea.Cmd
    switch m.activeView {
    case 0:
        m.listView, cmd = m.listView.Update(msg)
    case 1:
        m.detailView, cmd = m.detailView.Update(msg)
    case 2:
        m.searchView, cmd = m.searchView.Update(msg)
    }

    return m, cmd
}
```

---

## Memory Issues

### Issue: Memory Leak / Growing Memory Usage

**Symptoms:**
- Memory usage increases over time
- Never gets garbage collected

**Common Causes:**

1. **Goroutine Leaks**
   ```go
   // ❌ BAD - Goroutines never stop
   func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
       switch msg := msg.(type) {
       case tea.KeyMsg:
           if msg.String() == "s" {
               return m, func() tea.Msg {
                   go func() {
                       for {  // INFINITE LOOP!
                           time.Sleep(time.Second)
                           // Do something
                       }
                   }()
                   return nil
               }
           }
       }
       return m, nil
   }

   // ✅ GOOD - Use context for cancellation
   type model struct {
       ctx    context.Context
       cancel context.CancelFunc
   }

   func initialModel() model {
       ctx, cancel := context.WithCancel(context.Background())
       return model{ctx: ctx, cancel: cancel}
   }

   func worker(ctx context.Context) tea.Msg {
       for {
           select {
           case <-ctx.Done():
               return nil  // Stop gracefully
           case <-time.After(time.Second):
               // Do work
           }
       }
   }

   func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
       switch msg := msg.(type) {
       case tea.KeyMsg:
           if msg.String() == "q" {
               m.cancel()  // Stop all workers
               return m, tea.Quit
           }
       }
       return m, nil
   }
   ```

2. **Unreleased Resources**
   ```go
   // ❌ BAD
   func loadFile() tea.Msg {
       file, _ := os.Open("data.txt")
       // Never closed!
       data, _ := io.ReadAll(file)
       return dataMsg{data: data}
   }

   // ✅ GOOD
   func loadFile() tea.Msg {
       file, err := os.Open("data.txt")
       if err != nil {
           return errorMsg{err: err}
       }
       defer file.Close()  // Always close

       data, err := io.ReadAll(file)
       return dataMsg{data: data, err: err}
   }
   ```

---

## Testing Issues

### Issue: Hard to Test TUI

**Solution: Use teatest**

```go
import (
    "testing"
    tea "github.com/charmbracelet/bubbletea"
    "github.com/charmbracelet/bubbletea/teatest"
)

func TestNavigation(t *testing.T) {
    m := initialModel()

    // Create test program
    tm := teatest.NewTestModel(t, m)

    // Send key presses
    tm.Send(tea.KeyMsg{Type: tea.KeyDown})
    tm.Send(tea.KeyMsg{Type: tea.KeyDown})

    // Wait for program to process
    teatest.WaitFor(
        t, tm.Output(),
        func(bts []byte) bool {
            return bytes.Contains(bts, []byte("Item 2"))
        },
        teatest.WithCheckInterval(time.Millisecond*100),
        teatest.WithDuration(time.Second*3),
    )

    // Verify state
    finalModel := tm.FinalModel(t).(model)
    if finalModel.cursor != 2 {
        t.Errorf("Expected cursor at 2, got %d", finalModel.cursor)
    }
}
```

---

## Debugging Tips

### Enable Message Dumping

```go
import "github.com/davecgh/go-spew/spew"

type model struct {
    dump io.Writer
}

func main() {
    // Create debug file
    f, _ := os.Create("debug.log")
    defer f.Close()

    m := model{dump: f}
    p := tea.NewProgram(m)
    p.Start()
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    // Dump every message
    if m.dump != nil {
        spew.Fdump(m.dump, msg)
    }

    // ... rest of Update()
    return m, nil
}
```

### Live Reload with Air

`.air.toml`:
```toml
[build]
  cmd = "go build -o ./tmp/main ."
  bin = "tmp/main"
  include_ext = ["go"]
  exclude_dir = ["tmp"]
  delay = 1000
```

Run: `air`

---

## Quick Checklist

Before deploying your Bubble Tea app:

- [ ] No blocking operations in Update() or View()
- [ ] Terminal resize handled (tea.WindowSizeMsg)
- [ ] Panic recovery with terminal cleanup
- [ ] Dynamic layout (no hardcoded dimensions)
- [ ] Lipgloss padding/borders accounted for
- [ ] String operations use strings.Builder
- [ ] Goroutines have cancellation (context)
- [ ] Resources properly closed (defer)
- [ ] State machine handles message ordering
- [ ] Tests with teatest for key interactions

---

**Generated for Bubble Tea Maintenance Agent v1.0.0**
