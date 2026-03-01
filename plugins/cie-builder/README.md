# CIE Builder — Chuqlab Intelligence Engine

Guidance system for building the Chuqlab Intelligence Engine, a multi-tenant correctional intelligence platform for GovTech law enforcement.

## What It Does

CIE Builder guides Claude Code sessions through phased, TDD-driven development of a complete correctional intelligence platform on GCP. It:

1. **Detects build state** — knows exactly where the project stands
2. **Guides what to build next** — phased sprint planning
3. **Enforces TDD discipline** — failing tests first, always
4. **Enforces compliance from line one** — TX-RAMP Level 1 & CJIS controls baked in
5. **Adapts when direction changes** — surfaces implications, adjusts fast

## Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Go (Gin/Chi) |
| Frontend | TypeScript + React (Next.js) |
| Database | PostgreSQL (Cloud SQL/AlloyDB) |
| Vector DB | Ruvector |
| Media Storage | GCS |
| Transcription | Whisper Large (self-hosted on GKE GPU) |
| Queue | Pub/Sub |
| IaC | gcloud CLI |

## Phases

- **Phase 0** — Foundation: Auth, audit logging, GCP infra, Postgres schema
- **Phase 1** — Ingestion Pipeline: GCS buckets, CallEvent creation, Pub/Sub queue
- **Phase 2** — Transcription Engine: Whisper GPU deployment, worker service
- **Phase 3** — Vector Search & Linking: Ruvector, embeddings, semantic search
- **Phase 4** — Intelligence Layer: Alert engine, graph builder
- **Phase 5** — Investigator Experience: Chat (RAG), graph viz, case management
- **Phase 6** — Hardening & Certification Prep: TX-RAMP audit, pen testing, docs

## Installation

```bash
/plugin add Human-Frontier-Labs-Inc/human-frontier-labs-marketplace/cie-builder
```

## Activation Keywords

- "build CIE"
- "resume CIE work"
- "CIE architecture"
- "implement CIE phase"
- "CrimeMiner backend"
- "correctional audio pipeline"
- "Whisper transcription system"
- "Ruvector vector search"
- "investigative chat interface"
- "GovTech law enforcement platform"

## Files Structure

```
cie-builder/
├── SKILL.md                           # Full guidance system instructions
├── README.md                          # This file
├── VERSION                            # Version tracking
├── .claude-plugin/
│   └── marketplace.json               # Marketplace metadata
├── references/
│   ├── architecture.md                # Structural decisions guide
│   ├── compliance.md                  # TX-RAMP/CJIS control mapping
│   ├── phases.md                      # Full phase breakdown
│   ├── ruvector.md                    # Vector DB integration patterns
│   ├── stack-patterns.md              # Go/TS implementation conventions
│   └── txramp-level1-controls.md      # TX-RAMP Level 1 controls reference
└── scripts/
    └── detect-state.sh                # Build state detection script
```

## Compliance

Built-in enforcement for:
- **TX-RAMP Level 1** — Texas Risk and Authorization Management Program
- **CJIS Security Policy** — Criminal Justice Information Services

Controls are implemented from Phase 0, not bolted on later.

## License

MIT

## Author

Cornelius George — Chuqlab
