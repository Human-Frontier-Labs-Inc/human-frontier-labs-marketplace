# CIE Architecture Reference

## System Overview

The Chuqlab Intelligence Engine (CIE) is a multi-tenant, AI-native correctional intelligence platform. It ingests correctional audio/video, transcribes and translates via Whisper, embeds into Ruvector for semantic search, runs alerting intelligence, builds an evolving relationship graph, and provides a scoped investigative chat interface.

## Canonical Data Flow

```
Audio arrives (GCS vendor drop or manual upload)
  → Ingestion Poller detects new file
  → CallEvent created in Postgres
  → Job enqueued to Pub/Sub
  → Whisper Worker picks up job
  → Transcription + Translation generated
  → Transcript stored in Postgres
  → Chunks created (sliding window 400-600 tokens, 10-15% overlap)
  → Embeddings generated per chunk
  → Embeddings stored in Ruvector
  → Cross-call linking runs (similarity search)
  → Alert engine scans transcript (rules + ML)
  → Graph builder creates/updates nodes and edges
  → All data available via Chat RAG + Graph API + Search API
```

## CallEvent Schema

```sql
CREATE TABLE call_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(id),
    source_type     TEXT NOT NULL CHECK (source_type IN ('manual', 'vendor')),
    facility_id     TEXT NOT NULL,
    offender_id     TEXT,
    external_call_id TEXT,
    media_uri       TEXT NOT NULL,
    media_hash      TEXT NOT NULL,  -- SHA256 for idempotency
    timestamp_start TIMESTAMPTZ NOT NULL,
    timestamp_end   TIMESTAMPTZ,
    metadata_json   JSONB DEFAULT '{}',
    case_id         UUID REFERENCES cases(id),
    status          TEXT NOT NULL DEFAULT 'queued'
                    CHECK (status IN ('queued','processing','complete','failed')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Row-level security
ALTER TABLE call_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY call_events_org_isolation ON call_events
    USING (org_id = current_setting('app.current_org_id')::UUID);
```

## Multi-Tenant Isolation

Every layer enforces org_id:

| Layer | Isolation Mechanism |
|-------|-------------------|
| API | JWT contains org_id, middleware extracts and injects |
| Postgres | Row-level security policies on every table |
| GCS | Bucket namespace: `gs://cie-ingest-{org_id}/` |
| Ruvector | Org-scoped partitions/namespaces |
| Pub/Sub | Messages tagged with org_id, workers verify |

## SLA Targets

| Metric | Target |
|--------|--------|
| Ingestion to searchable | ≤ 60 minutes |
| Chat response | ≤ 5 seconds |
| Alert generation | ≤ 60 minutes from audio arrival |
| System uptime | 99.9% |

## Scalability Targets

- 140 facilities
- 2B minutes/year audio capacity
- 3-year data retention
- Horizontal scaling: GPU workers, API pods, Ruvector nodes

## Role Model

| Role | Permissions |
|------|------------|
| Investigator | Search, chat, view calls, view alerts, build cases |
| Intelligence Analyst | All Investigator + graph analysis, alert configuration |
| Supervisor | All Analyst + user management within org, reports |
| Admin | All Supervisor + org configuration, retention settings |
| Auditor | Read-only access to audit logs, compliance reports |

## Alert Tiers

**Tier 1 — Deterministic Rules**: Gang keywords, contraband, explicit violence, explicit suicide statements. Configurable per org.

**Tier 2 — ML Classifiers**: Violence planning risk score, suicide ideation risk score, third-party bridging probability, coercion likelihood.

Each alert: confidence score, triggered excerpt, timestamp, related entities.

## Graph Model

**Nodes**: inmate, phone_number, entity (names/locations/gang terms), facility, case

**Edges**: called, mentioned, linked_semantically, associated_with_case, related_to

**Edge Properties**: confidence_score, source_type (rule|ML|semantic), created_at, reinforcement_count

**Evolution**: Edges gain confidence when reinforced, decay when unreinforced, support time filtering.

## Chat System (RAG)

- Scoped to organization (mandatory) and optionally to case
- No external knowledge unless explicitly toggled
- Hybrid retrieval: Postgres filtering + Ruvector semantic search
- Responses MUST include: transcript excerpts, timestamps, confidence score, link to original audio, related entities
- Optional: timeline view, graph view
