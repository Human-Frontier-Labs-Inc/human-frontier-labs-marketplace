# CIE Stack Patterns & Conventions

## Go Backend Patterns

### Project Structure

```
engine/
├── cmd/
│   └── cie-api/          # Main API server entrypoint
│       └── main.go
├── internal/
│   ├── auth/             # Authentication + authorization
│   ├── audit/            # Audit logging
│   ├── ingest/           # Ingestion pipeline
│   ├── transcribe/       # Whisper worker orchestration
│   ├── embed/            # Embedding + Ruvector integration
│   ├── alert/            # Alert engine (rules + ML)
│   ├── graph/            # Graph builder + queries
│   ├── chat/             # RAG chat orchestrator
│   ├── export/           # PDF export
│   ├── middleware/        # HTTP middleware (auth, audit, CORS, etc.)
│   ├── model/            # Domain models (shared)
│   └── store/            # Database access layer
│       ├── postgres/     # Postgres implementations
│       └── ruvector/     # Ruvector implementations
├── pkg/
│   ├── gcp/              # GCS, Pub/Sub, KMS clients
│   └── config/           # Configuration loading
├── migrations/           # SQL migrations (golang-migrate)
├── go.mod
└── go.sum
```

### Router Selection

Use `chi` (lightweight, stdlib-compatible):

```go
r := chi.NewRouter()
r.Use(middleware.AuditLog)
r.Use(middleware.Authenticate)
r.Use(middleware.OrgScope)

r.Route("/api/v1", func(r chi.Router) {
    r.Post("/auth/login", auth.HandleLogin)
    r.With(middleware.RequireRole("admin")).Post("/admin/users", admin.HandleCreateUser)
})
```

### Database Access

Use `pgx` (native Postgres driver, no ORM):

```go
// Repository pattern — every method takes orgID from context
type CallEventRepo struct {
    pool *pgxpool.Pool
}

func (r *CallEventRepo) GetByID(ctx context.Context, id string) (*model.CallEvent, error) {
    orgID := middleware.OrgIDFromContext(ctx)
    row := r.pool.QueryRow(ctx,
        `SELECT * FROM call_events WHERE id = $1 AND org_id = $2`, id, orgID)
    // ...
}
```

### Configuration

Use environment variables with `envconfig`:

```go
type Config struct {
    Port        int    `envconfig:"PORT" default:"8080"`
    DatabaseURL string `envconfig:"DATABASE_URL" required:"true"`
    GCSBucket   string `envconfig:"GCS_BUCKET" required:"true"`
    PubSubTopic string `envconfig:"PUBSUB_TOPIC" required:"true"`
    JWTSecret   string `envconfig:"JWT_SECRET" required:"true"`
}
```

### Error Handling

Wrap errors with context, never expose internal details to client:

```go
// Internal: wrap with context
if err != nil {
    return fmt.Errorf("fetch call event %s: %w", id, err)
}

// API: map to HTTP status, generic message
func handleError(w http.ResponseWriter, err error) {
    switch {
    case errors.Is(err, ErrNotFound):
        http.Error(w, "resource not found", 404)
    case errors.Is(err, ErrForbidden):
        http.Error(w, "access denied", 403)
    default:
        http.Error(w, "internal error", 500)
    }
}
```

### Testing Conventions

```go
// Unit tests: _test.go in same package
func TestPasswordPolicy_Validate(t *testing.T) {
    policy := auth.DefaultPolicy()
    tests := []struct{
        name     string
        password string
        wantErr  bool
    }{
        {"too short", "abc", true},
        {"valid", "C0mpl3x!Pass#", false},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := policy.Validate(tt.password)
            if (err != nil) != tt.wantErr {
                t.Errorf("Validate(%q) error = %v, wantErr %v", tt.password, err, tt.wantErr)
            }
        })
    }
}

// Integration tests: separate _integration_test.go with build tag
//go:build integration
func TestIngestionPipeline_E2E(t *testing.T) {
    // Requires real GCS, Postgres, Pub/Sub
}
```

### Migrations

Use `golang-migrate`:

```bash
migrate create -ext sql -dir migrations -seq create_organizations
```

Every migration is a pair: `{N}_name.up.sql` and `{N}_name.down.sql`.

---

## TypeScript Frontend Patterns

### Project Structure

```
ui/
├── src/
│   ├── app/              # Next.js app router
│   │   ├── (auth)/       # Auth pages
│   │   ├── dashboard/    # Main dashboard
│   │   ├── chat/         # Chat interface
│   │   ├── graph/        # Graph visualization
│   │   └── cases/        # Case management
│   ├── components/       # Shared components
│   │   ├── ui/           # Primitives (button, input, etc.)
│   │   └── domain/       # Domain-specific (AlertCard, GraphNode, etc.)
│   ├── hooks/            # Custom hooks
│   ├── lib/              # Utilities, API client
│   │   ├── api.ts        # Typed API client
│   │   └── auth.ts       # Auth utilities
│   └── types/            # TypeScript types mirroring Go models
├── tests/
│   ├── unit/
│   └── e2e/
├── package.json
└── tsconfig.json
```

### API Client

Typed client mirroring Go API:

```typescript
// lib/api.ts
class CIEClient {
    private baseUrl: string;
    private token: string;

    async getCallEvent(id: string): Promise<CallEvent> {
        return this.get<CallEvent>(`/api/v1/calls/${id}`);
    }

    async searchTranscripts(query: SearchQuery): Promise<SearchResult[]> {
        return this.post<SearchResult[]>('/api/v1/search', query);
    }
}
```

### Testing

- Unit: Vitest
- E2E: Playwright
- Component: React Testing Library

---

## GCP Infrastructure Patterns

### gcloud CLI Scripts

All infra provisioned via shell scripts in `infra/`:

```
infra/
├── 00-project-setup.sh       # Project, APIs, service accounts
├── 01-networking.sh           # VPC, subnets, firewall
├── 02-database.sh             # Cloud SQL + schema
├── 03-storage.sh              # GCS buckets
├── 04-pubsub.sh               # Topics, subscriptions
├── 05-gke.sh                  # GKE cluster + node pools
├── 06-kms.sh                  # Key management
├── 07-deploy.sh               # Kubernetes manifests
├── teardown.sh                # Cleanup
└── env.sh                     # Shared environment variables
```

Every script is idempotent (can run twice safely). Every script logs what it creates.

### Naming Convention

```
cie-{resource}-{environment}
Example: cie-db-prod, cie-gke-staging, cie-ingest-org123
```

---

## Git Conventions

- Branch: `phase-{N}/sprint-{M}/{feature}`
- Commits: Conventional commits (`feat:`, `fix:`, `test:`, `docs:`, `infra:`)
- Tags: `phase-{N}-sprint-{M}` on sprint completion
- PRs: Required for main, reviewed by partner

## Dependency Policy

- Go: Only well-maintained, licensed dependencies. Run `govulncheck` in CI.
- TypeScript: Minimal dependencies. Run `npm audit` in CI.
- Container images: Pin versions, scan for CVEs.
