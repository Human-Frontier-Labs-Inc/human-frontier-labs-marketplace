# Effective Go — Full Pattern Reference

Detailed examples, edge cases, and rationale for every pattern in the skill. Cross-referenced with the official Effective Go guide at go.dev/doc/effective_go.

---

## 1. Package Naming

### Rules
- Lowercase, single word, no underscores, no mixedCaps
- The package name is the default qualifier — design for it
- Avoid collision with standard library names when you can
- Test files in `package foo_test` (external test package) are encouraged for API testing

### Extended Examples

```go
// bufio — the package name is the context
package bufio
type Reader struct{ ... }   // bufio.Reader — perfect
type Writer struct{ ... }   // bufio.Writer — perfect

// Wrong patterns
package util    // too generic, says nothing
package common  // same problem
package helper  // still nothing

// Correct: name for the domain
package auth
package billing
package inventory
```

### Import Aliases

When collision is unavoidable at the call site, the caller aliases:
```go
import (
    cryptorand "crypto/rand"
    mathrand   "math/rand"
)
```
This is the caller's burden, not a reason to rename your package.

---

## 2. Interface Design

### The io Package Model

Study `io` as the canonical example:
```go
type Reader interface { Read(p []byte) (n int, err error) }
type Writer interface { Write(p []byte) (n int, err error) }
type Closer interface { Close() error }
type Seeker interface { Seek(offset int64, whence int) (int64, error) }

// Composed interfaces
type ReadWriter    interface { Reader; Writer }
type ReadCloser    interface { Reader; Closer }
type WriteCloser   interface { Writer; Closer }
type ReadWriteCloser interface { Reader; Writer; Closer }
type ReadWriteSeeker interface { Reader; Writer; Seeker }
```

Every combination exists. Functions accept exactly what they need — nothing more.

### Interface Satisfaction at Compile Time

Assert interface satisfaction without allocating:
```go
// Compile-time check: does *Handler implement http.Handler?
var _ http.Handler = (*Handler)(nil)

// Useful in packages where you want early failure
var _ io.ReadWriter = (*MyBuffer)(nil)
```

Place these near the type definition.

### Interface Pollution Anti-Patterns

```go
// Anti-pattern: interface defined by the implementor, not the consumer
// This is how Java thinks. Go doesn't.
type UserService interface {
    GetUser(id string) (*User, error)
    CreateUser(u *User) error
    UpdateUser(u *User) error
    DeleteUser(id string) error
    ListUsers(filter Filter) ([]*User, error)
}

// Go way: define the interface at the consumer
// Your repository only needs to read? Define ReadableUserStore locally:
type UserReader interface {
    GetUser(id string) (*User, error)
}
// The concrete *UserRepository satisfies it implicitly.
```

---

## 3. Error Handling

### Sentinel Errors

Use `errors.Is` to check, not `==` (handles wrapping):
```go
var ErrNotFound = errors.New("not found")

if errors.Is(err, ErrNotFound) { ... }
```

### Custom Error Types

Implement `error` interface for structured errors:
```go
type ValidationError struct {
    Field   string
    Message string
}
func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation: %s — %s", e.Field, e.Message)
}

// Check with errors.As
var ve *ValidationError
if errors.As(err, &ve) {
    log.Printf("invalid field: %s", ve.Field)
}
```

### Error Wrapping Context

Add context at each layer using `%w`:
```go
func loadConfig(path string) (*Config, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return nil, fmt.Errorf("loadConfig: read %s: %w", path, err)
    }
    var cfg Config
    if err := json.Unmarshal(data, &cfg); err != nil {
        return nil, fmt.Errorf("loadConfig: parse %s: %w", path, err)
    }
    return &cfg, nil
}
```

The caller gets: `loadConfig: read /etc/app.json: open /etc/app.json: no such file or directory`

### Never Silently Discard

```go
// Wrong — swallowed error
_ = file.Close()

// Right — log if you can't return it
if err := file.Close(); err != nil {
    log.Printf("close %s: %v", file.Name(), err)
}

// In defer — capture to named return
func writeFile(path string, data []byte) (err error) {
    f, err := os.Create(path)
    if err != nil {
        return err
    }
    defer func() {
        if cerr := f.Close(); cerr != nil && err == nil {
            err = cerr
        }
    }()
    _, err = f.Write(data)
    return err
}
```

---

## 4. Zero-Value Design

### Standard Library Examples

- `sync.Mutex` — zero value is an unlocked mutex
- `bytes.Buffer` — zero value is an empty buffer ready to use
- `http.Client` — zero value uses default transport
- `sync.Once` — zero value has not yet executed

### Pointer vs Value Receivers

Zero-value works with value receivers on non-pointer types. If methods modify state, use pointer receivers consistently:
```go
// All pointer receivers — caller uses *T
type Counter struct{ n int }
func (c *Counter) Inc()      { c.n++ }
func (c *Counter) Value() int { return c.n }

// var c Counter works — c is addressable
var c Counter
c.Inc()
```

### Optional Configuration with Functional Options

When zero value is useful but configuration is needed:
```go
type Server struct {
    addr    string
    timeout time.Duration
    logger  *log.Logger
}

type Option func(*Server)

func WithTimeout(d time.Duration) Option {
    return func(s *Server) { s.timeout = d }
}
func WithLogger(l *log.Logger) Option {
    return func(s *Server) { s.logger = l }
}

func NewServer(addr string, opts ...Option) *Server {
    s := &Server{
        addr:    addr,
        timeout: 30 * time.Second,    // sensible default
        logger:  log.Default(),
    }
    for _, opt := range opts {
        opt(s)
    }
    return s
}
```

---

## 5. Concurrency Patterns

### Pipeline

```go
func generate(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        for _, n := range nums {
            out <- n
        }
        close(out)
    }()
    return out
}

func square(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for n := range in {
            out <- n * n
        }
        close(out)
    }()
    return out
}

// Usage
for n := range square(square(generate(2, 3))) {
    fmt.Println(n) // 16, 81
}
```

### Fan-out / Fan-in

```go
func merge(cs ...<-chan int) <-chan int {
    var wg sync.WaitGroup
    out := make(chan int)
    output := func(c <-chan int) {
        for n := range c {
            out <- n
        }
        wg.Done()
    }
    wg.Add(len(cs))
    for _, c := range cs {
        go output(c)
    }
    go func() {
        wg.Wait()
        close(out)
    }()
    return out
}
```

### Cancellation with Context

```go
func worker(ctx context.Context, jobs <-chan Job) error {
    for {
        select {
        case <-ctx.Done():
            return ctx.Err()
        case job, ok := <-jobs:
            if !ok {
                return nil
            }
            if err := process(job); err != nil {
                return fmt.Errorf("process job %v: %w", job.ID, err)
            }
        }
    }
}
```

Always propagate context as the first parameter. Never store context in a struct.

### When to Use Mutex vs Channel

| Situation | Use |
|-----------|-----|
| Protecting shared state (counter, map, cache) | `sync.Mutex` or `sync.RWMutex` |
| Passing data ownership between goroutines | Channel |
| Signaling an event (done, cancel) | Channel or `context.Context` |
| Waiting for multiple goroutines | `sync.WaitGroup` |
| One-time initialization | `sync.Once` |
| Bounding concurrency | Buffered channel as semaphore |

---

## 6. Embedding

### Interface Embedding

```go
// Promoting and extending interfaces
type ReadWriter interface {
    io.Reader
    io.Writer
}

// Add method to existing interface
type ReadWriterAt interface {
    io.ReaderAt
    io.WriterAt
}
```

### Struct Embedding — Ambiguity Resolution

When two embedded types have the same method name, the outer type must define it or the compiler errors:
```go
type Base1 struct{}
func (b Base1) Describe() string { return "base1" }

type Base2 struct{}
func (b Base2) Describe() string { return "base2" }

type Combined struct {
    Base1
    Base2
}
// combined.Describe() — compile error: ambiguous

// Fix: outer type defines the method
func (c Combined) Describe() string {
    return c.Base1.Describe() + "/" + c.Base2.Describe()
}
```

### Embedding for Mocking in Tests

```go
// Embed the real client, override only the method you need in tests
type mockClient struct {
    *RealClient            // satisfies full interface
    fetchFn func(string) ([]byte, error)
}
func (m *mockClient) Fetch(url string) ([]byte, error) {
    if m.fetchFn != nil {
        return m.fetchFn(url)
    }
    return m.RealClient.Fetch(url)
}
```

---

## 7. Composite Literals

### Struct with All Fields

```go
// Named fields — always use these outside the defining package
type Config struct {
    Host    string
    Port    int
    TLS     bool
    Timeout time.Duration
}

cfg := Config{
    Host:    "localhost",
    Port:    8080,
    TLS:     true,
    Timeout: 10 * time.Second,
}
```

### Slice of Structs

```go
routes := []Route{
    {Method: "GET",  Path: "/health",  Handler: healthHandler},
    {Method: "POST", Path: "/users",   Handler: createUser},
    {Method: "GET",  Path: "/users",   Handler: listUsers},
}
```

### Nested Literals

```go
req := &http.Request{
    Method: "POST",
    URL:    &url.URL{Scheme: "https", Host: "api.example.com", Path: "/v1/data"},
    Header: http.Header{
        "Content-Type": {"application/json"},
        "X-API-Key":    {apiKey},
    },
}
```

---

## 8. `new` vs `make` — Edge Cases

```go
// new — zeroed allocation, returns pointer
p := new(sync.Mutex)   // *sync.Mutex, unlocked
n := new(int)          // *int, value 0
s := new([]string)     // *[]string pointing to nil slice — unusual, rarely needed

// make — slice, map, channel only
slice := make([]int, 5)          // len=5, cap=5, all zeros
slice2 := make([]int, 0, 100)    // len=0, cap=100 — pre-allocated
m := make(map[string]int)        // initialized, ready to write
ch := make(chan struct{})         // unbuffered signal channel
bch := make(chan []byte, 10)      // buffered channel

// Literal initialization — often preferred over make
m2 := map[string]int{}           // equivalent to make(map[string]int)
s2 := []int{}                    // equivalent to make([]int, 0)
// But: make is preferred when capacity hint is meaningful
```

---

## 9 & 10. Naming: Getters and Interfaces

### Getter Naming Full Reference

```go
type Person struct {
    firstName string
    lastName  string
    age       int
}

// Correct
func (p *Person) FirstName() string      { return p.firstName }
func (p *Person) SetFirstName(s string)  { p.firstName = s }
func (p *Person) Age() int               { return p.age }
func (p *Person) SetAge(n int)           { p.age = n }

// Wrong
func (p *Person) GetFirstName() string   { } // never
func (p *Person) GetAge() int            { } // never
```

### Interface Naming — Full -er List from stdlib

| Interface | Method | Package |
|-----------|--------|---------|
| `Reader` | `Read` | `io` |
| `Writer` | `Write` | `io` |
| `Closer` | `Close` | `io` |
| `Seeker` | `Seek` | `io` |
| `Stringer` | `String` | `fmt` |
| `Error` | `Error` | builtin |
| `Handler` | `ServeHTTP` | `net/http` |
| `Marshaler` | `MarshalJSON` | `encoding/json` |
| `Unmarshaler` | `UnmarshalJSON` | `encoding/json` |

When the natural -er doesn't work (e.g., `Manage` → `Manager` is fine, but `Execute` → `Executer` is awkward), use role names: `Executor`, `Processor`, `Dispatcher`.

---

## 11. Defer — Full Pattern Reference

### Resource Cleanup Chain

```go
func copyFile(dst, src string) error {
    in, err := os.Open(src)
    if err != nil {
        return err
    }
    defer in.Close()  // immediately after open

    out, err := os.Create(dst)
    if err != nil {
        return err
    }
    defer out.Close()  // immediately after create

    _, err = io.Copy(out, in)
    return err
}
```

### Defer in Loops — Wrong Pattern

```go
// Wrong — all files stay open until function returns
func processFiles(paths []string) error {
    for _, path := range paths {
        f, err := os.Open(path)
        if err != nil {
            return err
        }
        defer f.Close()  // deferred, not closed per iteration
        process(f)
    }
    return nil
}

// Right — extract to function
func processFiles(paths []string) error {
    for _, path := range paths {
        if err := processOne(path); err != nil {
            return err
        }
    }
    return nil
}
func processOne(path string) error {
    f, err := os.Open(path)
    if err != nil {
        return err
    }
    defer f.Close()
    return process(f)
}
```

### Defer for Timing and Tracing

```go
func expensive() {
    defer func(start time.Time) {
        log.Printf("expensive took %v", time.Since(start))
    }(time.Now())
    // ... do work
}
```

---

## 12. Accept Interfaces, Return Structs — Edge Cases

### When to Return an Interface

Returning an interface is appropriate when:
1. The implementation may change and you want to hide it
2. You're returning one of several concrete types based on runtime conditions
3. The type is genuinely abstract (e.g., `error`)

```go
// Acceptable — error is always an interface
func parse(s string) (int, error) { ... }

// Acceptable — returning different implementations
func NewLogger(kind string) Logger {
    switch kind {
    case "json":   return &JSONLogger{}
    case "text":   return &TextLogger{}
    default:       return &NoopLogger{}
    }
}
```

### Narrowest Interface at Call Site

```go
// io.Copy only needs Reader on the source side
func backup(dst io.Writer, src io.Reader) error {
    _, err := io.Copy(dst, src)
    return err
}
// Accepts *os.File, *bytes.Buffer, *http.Response.Body, net.Conn, anything
```

---

## 13. Constructor Naming — Full Reference

```go
// Package has one primary exported type
package ring
func New(n int) *Ring { ... }          // ring.New(5)

// Package has multiple exported types — use New<Type>
package multipart
func NewReader(r io.Reader, boundary string) *Reader { ... }
func NewWriter(w io.Writer) *Writer { ... }

// Wrong: stutter
package list
func NewList() *List { ... }           // list.NewList — redundant
// Right:
func New() *List { ... }               // list.New

// Constructors for embedding targets often take options
package server
func New(addr string, opts ...Option) *Server { ... }
```

---

## 14. Type Conversions — Full Patterns

### sort.Interface via Named Type

```go
type ByLength []string

func (s ByLength) Len() int           { return len(s) }
func (s ByLength) Less(i, j int) bool { return len(s[i]) < len(s[j]) }
func (s ByLength) Swap(i, j int)      { s[i], s[j] = s[j], s[i] }

words := []string{"peach", "kiwi", "pear"}
sort.Sort(ByLength(words))  // convert []string to ByLength at call site
```

Modern Go (1.21+) prefers `sort.Slice`:
```go
sort.Slice(words, func(i, j int) bool {
    return len(words[i]) < len(words[j])
})
```

### Type Assertion vs Type Conversion

```go
// Type conversion — between compatible types at compile time
var i int = 42
var f float64 = float64(i)

// Type assertion — interface to concrete type at runtime
var r io.Reader = &bytes.Buffer{}
buf, ok := r.(*bytes.Buffer)  // always use the two-value form
if ok {
    buf.Reset()
}

// Type switch — when handling multiple types
func describe(i interface{}) string {
    switch v := i.(type) {
    case int:     return fmt.Sprintf("int: %d", v)
    case string:  return fmt.Sprintf("string: %q", v)
    case bool:    return fmt.Sprintf("bool: %t", v)
    default:      return fmt.Sprintf("unknown: %T", v)
    }
}
```

---

## Additional Patterns Not in Effective Go (But Essential)

### Table-Driven Tests

```go
func TestAdd(t *testing.T) {
    tests := []struct {
        name     string
        a, b     int
        expected int
    }{
        {"positive", 1, 2, 3},
        {"negative", -1, -2, -3},
        {"zero", 0, 0, 0},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := Add(tt.a, tt.b)
            if got != tt.expected {
                t.Errorf("Add(%d, %d) = %d, want %d", tt.a, tt.b, got, tt.expected)
            }
        })
    }
}
```

### Context Propagation

```go
// Always first parameter, always named ctx
func (s *Service) FetchUser(ctx context.Context, id string) (*User, error) { ... }

// Never store context in a struct
type Handler struct {
    ctx context.Context  // Wrong
}

// Pass it at call time
type Handler struct {
    db *sql.DB  // Right — store dependencies, not contexts
}
func (h *Handler) Handle(ctx context.Context, req Request) Response { ... }
```

### init() Usage

Only use `init()` for:
1. Registering drivers, codecs, or plugins (e.g., `database/sql` drivers)
2. Verifying/fixing program state that cannot be checked at compile time

Never use `init()` for:
- Setting package-level variables that could be constants
- Anything that can fail (you can't return an error from `init`)
- Side effects that surprise users of the package

### Blank Identifier for Side Effects

```go
import _ "net/http/pprof"     // registers pprof handlers as side effect
import _ "image/png"          // registers PNG decoder
```

This is the canonical pattern for plugin registration.

---

## References

- go.dev/doc/effective_go — Official Effective Go guide
- go.dev/wiki/CodeReviewComments — Supplement to Effective Go
- pkg.go.dev/io — Study the io package as the canonical interface design example
- go.dev/blog/pipelines — Concurrency pipeline patterns
- go.dev/blog/context — Context usage guidance
