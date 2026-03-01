# CIE Build Phases — Detailed Breakdown

## Phase 0: Foundation (Sprints 1-2)

### Sprint 1: Project Scaffold + GCP Infra

**Goal**: Repo exists, CI passes, GCP resources provisioned, basic API deploys.

**Tasks**:
1. Initialize Go module (`cie-engine/`) and TypeScript project (`cie-ui/`)
2. Set up monorepo structure:
   ```
   cie/
   ├── engine/          # Go backend
   │   ├── cmd/         # Entrypoints
   │   ├── internal/    # Business logic
   │   ├── pkg/         # Shared packages
   │   └── go.mod
   ├── ui/              # TypeScript/React frontend
   │   ├── src/
   │   └── package.json
   ├── infra/           # gcloud CLI scripts
   ├── docs/
   ├── BUILD_STATE.md
   └── PHASE_TRACKER.md
   ```
3. GCP provisioning via gcloud CLI:
   - GKE cluster (standard node pool + GPU node pool placeholder)
   - Cloud SQL PostgreSQL instance (HA, encrypted)
   - GCS buckets (per-tenant namespace pattern)
   - Pub/Sub topics and subscriptions
   - IAM roles and service accounts
   - VPC + firewall rules
   - Cloud Armor (DDoS protection) — satisfies SC-05
4. Dockerfile for Go API
5. CI pipeline (Cloud Build or GitHub Actions)
6. Basic health check endpoint deployed to GKE

**Tests**:
- Unit: gcloud script idempotency (can run twice without error)
- Integration: Health endpoint responds 200

**Compliance Controls Satisfied**:
- CM-02 (Baseline Configuration) — IaC scripts define baseline
- SC-05 (DoS Protection) — Cloud Armor
- SC-07 (Boundary Protection) — VPC + firewall
- SC-22 (DNS architecture) — Cloud DNS config
- CM-08 (Component Inventory) — GCP resource manifest

**Deliverable**: `gcloud` scripts provision full GCP environment. Go API deploys and responds.

---

### Sprint 2: Auth, RBAC, Audit Logging

**Goal**: Users can authenticate, roles are enforced, every action is logged.

**Tasks**:
1. Postgres schema for auth:
   - `organizations` (multi-tenant root)
   - `users` (linked to org)
   - `roles` (Investigator, Analyst, Supervisor, Admin, Auditor)
   - `user_roles` (many-to-many)
   - `sessions`
   - `audit_logs`
2. Auth system:
   - Password-based auth with bcrypt
   - MFA support (TOTP) — required for privileged accounts
   - JWT token issuance with org_id claim
   - Session management with configurable timeout
   - Re-authentication for sensitive operations
   - Failed login lockout (max 5 attempts / 15 min)
3. RBAC middleware:
   - Extract org_id from JWT
   - Enforce role-based access on every endpoint
   - Row-level security in Postgres (org_id WHERE clause on every query)
4. Audit logging:
   - Structured JSON logs
   - Every API call logged: who, what, when, from where
   - Append-only audit table in Postgres
   - Log protection (AU-09): separate write-only service account
5. API endpoints:
   - POST /auth/login
   - POST /auth/mfa/verify
   - POST /auth/logout
   - GET /auth/me
   - POST /admin/users (Admin only)
   - GET /admin/audit-logs (Auditor only)

**Tests**:
- Unit: Password hashing, JWT creation/validation, role checking
- Unit: Audit log entry creation, tamper detection
- Integration: Login → MFA → access protected endpoint → verify audit log
- Integration: Wrong password 5x → account locked
- Integration: Cross-org access denied

**Compliance Controls Satisfied**:
- AC-02 (Account Management) — full user lifecycle
- AC-03 (Access Enforcement) — RBAC + row-level security
- AC-07 (Unsuccessful Logon Attempts) — lockout policy
- IA-02 (Identification and Authentication) — auth system
- IA-02-01 (MFA for Privileged Accounts) — TOTP
- IA-05 (Authenticator Management) — password policy
- IA-05-01 (Password-based Auth) — complexity, rotation
- IA-06 (Authentication Feedback) — no password hints
- IA-11 (Re-authentication) — sensitive ops require re-auth
- AU-02 (Event Logging) — comprehensive audit
- AU-03 (Content of Audit Records) — structured format
- AU-09 (Protection of Audit Information) — append-only, separate SA
- AU-12 (Audit Record Generation) — every API call

**Deliverable**: Authenticated, role-controlled API with full audit trail.

---

## Phase 1: Ingestion Pipeline (Sprints 3-4)

### Sprint 3: GCS Ingestion + CallEvent Pipeline

**Goal**: Files arrive in GCS → CallEvents created → Jobs queued.

**Tasks**:
1. GCS bucket structure:
   ```
   gs://cie-ingest-{org_id}/facility/{facility_id}/YYYY/MM/DD/*.wav
   ```
2. Ingestion poller service (Go):
   - Runs on configurable schedule (hourly default)
   - Detects new files via GCS listing + last-processed watermark
   - Parses metadata JSON sidecar files
   - Creates canonical CallEvent in Postgres
   - Idempotency: SHA256 of media_uri prevents double-processing
   - Enqueues Pub/Sub message with CallEvent ID
3. Postgres schema additions:
   - `call_events` table (per canonical schema)
   - `processing_jobs` table (tracks job lifecycle)
4. Pub/Sub integration:
   - Topic: `cie-transcription-jobs`
   - Dead letter topic for failed jobs
   - Retry policy with exponential backoff

**Tests**:
- Unit: Metadata parsing, idempotency check, CallEvent creation
- Integration: File in GCS → poller detects → CallEvent in DB → Pub/Sub message published
- Integration: Same file twice → only one CallEvent created
- Integration: Malformed metadata → job marked failed, audit logged

**Compliance Controls Satisfied**:
- AU-02 (Event Logging) — ingestion events logged
- CM-07 (Least Functionality) — poller does one thing
- SI-04 (System Monitoring) — job status tracking

**Deliverable**: Poller detects files, creates CallEvents, enqueues jobs.

---

### Sprint 4: Manual Upload + Unified Pipeline

**Goal**: Users can upload audio via API, enters same pipeline as vendor drop.

**Tasks**:
1. Upload endpoint:
   - POST /api/v1/uploads (multipart file)
   - Validates file type (wav, mp3, mp4, etc.)
   - Stores in GCS under user's org namespace
   - Creates CallEvent with source_type=manual
   - Optional case_id attachment
   - File size limits enforced
2. Unified downstream:
   - Manual uploads produce identical CallEvents
   - Same Pub/Sub enqueue
   - No deviation in processing path
3. Upload status tracking:
   - GET /api/v1/uploads/{id}/status
   - WebSocket or polling for real-time status

**Tests**:
- Unit: File validation, size limits, type checking
- Integration: Upload file → CallEvent created → Pub/Sub message → status trackable
- Integration: Oversized file rejected with proper error
- Integration: Upload without auth → 401

**Compliance Controls Satisfied**:
- AC-03 (Access Enforcement) — upload requires auth + correct role
- MP-07 (Media Use) — file type restrictions
- SI-03 (Malicious Code Protection) — file validation

**Deliverable**: Manual upload works, enters same pipeline as vendor ingest.

---

## Phase 2: Transcription Engine (Sprints 5-6)

### Sprint 5: Whisper GPU Deployment + Worker Service

**Goal**: Whisper model deployed on GKE GPU, workers consume jobs.

**Tasks**:
1. GKE GPU node pool:
   - Node type: NVIDIA L4 or T4 (cost-optimized for batch)
   - Autoscaling: 0 to N based on queue depth
   - Preemptible/spot instances for cost savings
   - gcloud CLI scripts for provisioning
2. Whisper container:
   - Docker image with Whisper large multilingual
   - gRPC or REST API for transcription requests
   - Health check + readiness probes
3. Worker service (Go):
   - Subscribes to `cie-transcription-jobs`
   - Pulls audio from GCS
   - Sends to Whisper for transcription + translation
   - Handles timeouts and retries
   - Updates CallEvent status (queued → processing → complete/failed)
4. ≤60-minute SLA enforcement:
   - Job age monitoring
   - Alerts if jobs exceed SLA

**Tests**:
- Unit: Worker job lifecycle state machine
- Unit: Timeout handling, retry logic
- Integration: Pub/Sub message → worker picks up → calls Whisper → updates status
  (Note: requires real audio fixture from team — skip if not available)

**Compliance Controls Satisfied**:
- AU-02 — processing events logged
- CP-10 (Recovery) — worker restarts cleanly from crashes
- SI-04 (Monitoring) — SLA monitoring

**Deliverable**: Whisper on GPU, workers process queued jobs.

---

### Sprint 6: Chunking, Transcript Storage, Translation

**Goal**: Transcripts chunked, stored in Postgres, English translations generated.

**Tasks**:
1. Chunking service:
   - Sliding window: 400-600 tokens
   - 10-15% overlap
   - Preserves timestamp alignment
2. Postgres schema:
   - `transcripts` (full transcript per call)
   - `transcript_chunks` (individual chunks with timestamps)
3. Translation pipeline:
   - Whisper generates native + English translation
   - Both stored
   - Language detection metadata
4. Processing completion:
   - CallEvent status → complete
   - Chunk count and metadata recorded

**Tests**:
- Unit: Chunking algorithm (correct window sizes, overlap, timestamp preservation)
- Unit: Transcript storage and retrieval
- Integration: Full pipeline — audio → transcription → chunking → storage

**Compliance Controls Satisfied**:
- AU-04 (Audit Log Storage) — transcript retention configurable
- AU-11 (Audit Record Retention) — configurable per tenant
- SI-12 (Information Retention) — retention model

**Deliverable**: Audio → transcription → chunked → stored with translations.

---

## Phase 3: Vector Search & Linking (Sprints 7-8)

### Sprint 7: Ruvector Integration + Embedding Pipeline

**Goal**: Chunks embedded and stored in Ruvector, searchable.

**Tasks**:
1. Study Ruvector repo (clone and read first):
   ```bash
   git clone https://github.com/ruvnet/ruvector /tmp/ruvector-ref
   ```
2. Deploy Ruvector cluster (containerized on GKE)
3. Embedding service (Go):
   - Takes transcript chunks
   - Generates embeddings (model TBD based on Ruvector requirements)
   - Stores in Ruvector with metadata: org_id, facility_id, offender_id, timestamp_range, entity_tags
4. Ruvector partitioning:
   - Per-org namespace/partition
   - Enforced at query time
5. Semantic search API:
   - POST /api/v1/search
   - Input: query text, org_id (from JWT), optional filters
   - Output: ranked chunks with scores, timestamps, call references

**Tests**:
- Unit: Embedding generation, metadata attachment
- Unit: Org-scoped query filtering
- Integration: Store chunk → search by text → retrieve with correct metadata
- Integration: Cross-org search isolation (org A can't see org B)

**Compliance Controls Satisfied**:
- AC-03 — org-scoped vector partitioning
- SC-28 (Protection at Rest) — encrypted Ruvector storage
- SC-39 (Process Isolation) — tenant isolation in vector space

**Deliverable**: Chunks embedded, stored in Ruvector, searchable with org isolation.

---

### Sprint 8: Automatic Cross-Call Linking

**Goal**: New transcripts automatically find related past conversations.

**Tasks**:
1. Cross-call linker service:
   - Triggered after embedding storage
   - Queries Ruvector for similar chunks (same org)
   - Configurable similarity threshold
   - Creates "Related Conversations" records in Postgres
2. Linking results:
   - Related call pairs with confidence scores
   - Bidirectional linking
3. API endpoint:
   - GET /api/v1/calls/{id}/related
   - Returns related calls with scores and excerpts

**Tests**:
- Unit: Similarity threshold logic
- Unit: Bidirectional link creation
- Integration: Two related calls → auto-linked with correct confidence

**Deliverable**: New transcripts auto-link to related past conversations.

---

## Phase 4: Intelligence Layer (Sprints 9-10)

### Sprint 9: Alert Engine

**Goal**: Rules and ML classifiers generate alerts from transcripts.

**Tasks**:
1. Tier 1 — Rule-based alerts:
   - Configurable keyword/pattern watchlists per org
   - Categories: gang keywords, contraband, explicit violence, suicide statements
   - Pattern matching on transcript text
2. Tier 2 — ML classifiers:
   - Pre-trained models for: violence risk, suicide ideation, third-party bridging
   - Confidence scoring
3. Alert storage:
   - `alerts` table: risk_score, confidence, trigger_excerpt, timestamp, source_type, related_entities
4. Alert fatigue prevention:
   - Configurable threshold gating per org
   - Aggregated alert views
   - Analyst sensitivity controls
5. API endpoints:
   - GET /api/v1/alerts (filtered by org, facility, date range, severity)
   - PUT /api/v1/alerts/{id}/acknowledge
   - GET /api/v1/alerts/stats

**Tests**:
- Unit: Keyword matching, pattern rules
- Unit: Alert deduplication and aggregation
- Integration: Transcript with trigger content → alert generated with correct metadata
- Integration: Below-threshold content → no alert

**Compliance Controls Satisfied**:
- IR-04 (Incident Handling) — alerts as incident triggers
- IR-05 (Incident Monitoring) — alert monitoring dashboard
- SI-04 (System Monitoring) — continuous monitoring via alerts

**Deliverable**: Alerts fire on transcripts via rules and ML. Fatigue controls work.

---

### Sprint 10: Graph Builder + Evolution

**Goal**: Relationship graph builds from calls, alerts, and links.

**Tasks**:
1. Graph data model in Postgres:
   - `graph_nodes`: inmate, phone_number, entity, facility, case
   - `graph_edges`: called, mentioned, linked_semantically, associated_with_case, related_to
   - Edge attributes: confidence_score, source_type, created_at, reinforcement_count
2. Graph builder service:
   - Extracts entities from transcripts
   - Creates/updates nodes
   - Creates edges from: calls, mentions, semantic links, alerts
3. Graph evolution:
   - Reinforcement: repeated connections increase confidence
   - Decay: unreinforced edges decay over configurable period
   - Time filtering support
4. API endpoints:
   - GET /api/v1/graph/nodes/{id}/neighbors
   - GET /api/v1/graph/search?entity=X
   - GET /api/v1/graph/subgraph?center={id}&depth={N}

**Tests**:
- Unit: Node/edge creation, reinforcement logic, decay calculation
- Unit: Entity extraction patterns
- Integration: Calls processed → graph nodes/edges created → queryable
- Integration: Same entities across calls → edge reinforcement increases confidence

**Deliverable**: Graph builds from data, evolves over time, queryable via API.

---

## Phase 5: Investigator Experience (Sprints 11-12)

### Sprint 11: RAG Chat Interface

**Goal**: Investigators chat with scoped AI that cites internal evidence.

**Tasks**:
1. Chat orchestrator (Go):
   - Accepts user query + scope (org-wide or case-specific)
   - Hybrid retrieval: Postgres filters + Ruvector semantic search
   - Context assembly with transcript excerpts
   - LLM response generation (Claude API)
   - Evidence injection: timestamps, confidence, audio links, related entities
2. Chat constraints:
   - No external knowledge unless explicitly toggled
   - All claims must cite transcript evidence
   - Confidence scoring on responses
3. Chat API:
   - POST /api/v1/chat/message
   - GET /api/v1/chat/history/{session_id}
4. Frontend chat component (TypeScript/React):
   - Message input with scope selector
   - Response display with evidence cards
   - Timeline view option
   - Graph view option

**Tests**:
- Unit: Context assembly, evidence injection, scope filtering
- Unit: External knowledge toggle enforcement
- Integration: Query → retrieval → response with citations → timestamps correct

**Deliverable**: Working investigative chat with cited evidence.

---

### Sprint 12: Graph Viz, Case Management, Export

**Goal**: Full investigator workflow from search to court-ready export.

**Tasks**:
1. Graph visualization (React):
   - Interactive node-edge display
   - Click-to-expand neighborhoods
   - Time slider filtering
   - Color coding by node/edge type
2. Case management:
   - Create/update cases
   - Attach calls, alerts, graph segments to cases
   - Case timeline view
3. PDF export:
   - Case evidence packet generation
   - Includes: transcripts, alerts, graph snapshots, timeline
   - Formatted for court/legal review
4. API endpoints:
   - CRUD for cases
   - POST /api/v1/cases/{id}/export

**Tests**:
- Unit: PDF generation with correct content
- Unit: Case association logic
- Integration: Create case → attach evidence → export PDF → verify contents

**Deliverable**: Complete investigator workflow. Search → investigate → build case → export.

---

## Phase 6: Hardening & Certification Prep (Sprints 13-14)

### Sprint 13: Security Hardening

**Goal**: Pen test ready, all TX-RAMP Level 1 controls verified.

**Tasks**:
1. Walk through every TX-RAMP Level 1 control in `references/compliance.md`
2. Verify implementation or document compensating controls
3. Vulnerability scanning (RA-05)
4. Penetration testing scenarios
5. Encryption verification (at rest + in transit)
6. Access control audit
7. Audit log integrity verification

### Sprint 14: Documentation & Load Testing

**Goal**: System is certification-ready with complete documentation.

**Tasks**:
1. System Security Plan (SSP) draft
2. Architecture documentation
3. API documentation (OpenAPI spec)
4. Operations runbook
5. Load testing at scale targets (140 facilities, projected volumes)
6. Performance optimization based on load test results
7. Disaster recovery testing (CP-02, CP-04)

**Deliverable**: TX-RAMP Level 1 certification-ready package.
