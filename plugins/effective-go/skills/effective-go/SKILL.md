---
name: effective-go
description: Idiomatic Go architecture and design. Use whenever writing Go code, designing Go packages, or helping with Go projects. Focuses on what makes Go code structurally different from other languages -- zero-value types, consumer-defined interfaces, composition via embedding. Triggers on any Go code generation, package design, or architecture discussion.
---

# Effective Go -- What You Don't Already Know

You already write syntactically correct Go. You use named fields, defer after acquisition, guard clauses, `fmt.Errorf` wrapping. That's not the problem.

The problem is **architectural taste** -- the design decisions that happen before and during coding that make Go programs feel like Go, not translated Java. This skill focuses exclusively on those decisions.

## 1. Zero-Value Design (most commonly missed)

Every struct you define: ask "does `var x MyType` work?" If calling a method on a zero-value instance panics or does nothing useful, redesign.

**The pattern:** lazy-initialize maps and slices on first write. Use nil pointers to mean "use default." Design so `new(T)` returns something usable.

```go
type Store struct {
    mu    sync.RWMutex
    items map[string]*Item  // nil is fine -- lazy-init on write
}

func (s *Store) Put(key string, item *Item) {
    s.mu.Lock()
    defer s.mu.Unlock()
    if s.items == nil {
        s.items = make(map[string]*Item)
    }
    s.items[key] = item
}

func (s *Store) Get(key string) (*Item, bool) {
    s.mu.RLock()
    defer s.mu.RUnlock()
    item, ok := s.items[key]  // nil map read returns zero value -- safe
    return item, ok
}
```

Standard library examples: `bytes.Buffer`, `sync.Mutex`, `http.Client` -- all usable at zero value. Design your types the same way.

When a constructor IS required (network connections, validated config), that's fine -- but it should be the exception. Name it `New` (one type per package) or `NewThing` (multiple types).

## 2. Interface Discovery (biggest architectural difference from Java/Python)

In Go, interfaces are defined where they're **consumed**, not where they're **implemented**. This is the single most important Go design principle and the one most commonly violated.

**The process:**
1. You have a function that needs to call methods on something
2. What methods does it actually call? One? Two?
3. Define a 1-2 method interface right there, in the consuming package
4. The concrete type satisfies it implicitly -- no `implements` keyword

```go
// Your handler package needs to fetch users. It calls ONE method.
// Define the interface HERE, not in the database package.
type UserFetcher interface {
    Fetch(ctx context.Context, id string) (*User, error)
}

func HandleGetUser(store UserFetcher, id string) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        user, err := store.Fetch(r.Context(), id)
        // ...
    }
}
```

**Why this matters:** any concrete type with a `Fetch` method works. Your database implementation, a mock for tests, a cache wrapper -- they all satisfy `UserFetcher` without knowing it exists.

**Red flags you're doing it wrong:**
- An interface with 5+ methods
- An interface defined in the same package as its only implementation
- An interface named `IFoo` or `FooInterface`
- A function accepting a concrete type it could accept as an interface

**Accept interfaces, return structs.** Your function parameters should be narrow interfaces. Your return types should be concrete structs so callers get the full API.

## 3. Composition via Embedding (Go's alternative to inheritance)

Embed a type to promote ALL its methods to the outer type. This is how Go does composition -- no inheritance, no subclassing, just automatic delegation.

**When to embed:**

```go
// Wrap http.ServeMux with extra behavior
type Server struct {
    *http.ServeMux  // promotes Handle, HandleFunc, ServeHTTP
    timeout time.Duration
}

// Add logging to any type
type Service struct {
    *log.Logger  // promotes Print, Printf, Println, etc.
    db *sql.DB
}
svc.Println("starting up...")  // calls the embedded Logger

// Compose interfaces
type ReadWriteCloser interface {
    io.Reader
    io.Writer
    io.Closer
}

// Test mocks -- satisfy a big interface, override 1-2 methods
type mockDB struct {
    *RealDB                    // satisfies everything
    fetchFn func(string) *User // override just Fetch
}
func (m *mockDB) Fetch(id string) *User { return m.fetchFn(id) }
```

**When NOT to embed:** if you only need 1-2 methods from the embedded type, write explicit forwarding instead. Embedding promotes everything, which can expose methods you didn't intend.

## 4. Named Types for Value Sets

Any finite set of known values (event types, states, statuses) gets a named type. Never use raw strings.

```go
type Status string
const (
    StatusPending  Status = "pending"
    StatusRunning  Status = "running"
    StatusComplete Status = "complete"
    StatusFailed   Status = "failed"
)

// Now the compiler helps you -- you can't accidentally pass "pneding"
func (j *Job) SetStatus(s Status) { j.status = s }
```

This applies to event types, states, categories, roles -- anything where the set of valid values is known at design time.

## 5. Use the Standard Library

Before writing a loop, check if the standard library already does it. Go developers reach for `sort.Slice`, `slices.SortFunc`, `strings.Builder`, `maps.Keys`, `sync.Pool` without thinking. If you find yourself implementing something that sounds like it should exist, it does.

Never hand-roll sorting. Never reimplement string joining. Never build your own sync primitives.

## Hard Rules

These are non-negotiable tells that code wasn't written by a Go developer:

- **No `os.Exit()` outside `main()`** -- return errors up the stack
- **No `GetFoo()` getters** -- the getter for `name` is `Name()`, setter is `SetName()`
- **No concrete dependency parameters** -- any function accepting a store, client, or service takes a narrow interface defined in the consuming package, not the concrete type
- **No leaked concrete types in interfaces** -- if an interface method returns `*ssh.Session`, it's not really an interface. Return `io.Reader` or `io.ReadCloser`
- **Domain types match the domain** -- ports are `int`, timestamps are `time.Time`, not strings

For full pattern reference: `references/effective-go-patterns.md`
