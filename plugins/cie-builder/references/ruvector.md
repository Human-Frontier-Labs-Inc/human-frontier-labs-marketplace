# Ruvector Integration Reference

## Important: Study Before Use

Before ANY Ruvector implementation work, clone and study the repo:

```bash
git clone https://github.com/ruvnet/ruvector /tmp/ruvector-ref
cat /tmp/ruvector-ref/README.md
ls /tmp/ruvector-ref/
# Read source code, understand API, find examples
```

This step is NOT optional. Ruvector's API and capabilities may have evolved. Always read the latest source before coding against it.

## CIE's Use of Ruvector

### What Goes Into Ruvector

Each transcript chunk produces one Ruvector entry:

```json
{
    "id": "chunk-uuid",
    "vector": [0.123, -0.456, ...],
    "metadata": {
        "org_id": "org-uuid",
        "facility_id": "facility-123",
        "call_event_id": "call-uuid",
        "offender_id": "offender-456",
        "timestamp_start": "2025-01-15T10:30:00Z",
        "timestamp_end": "2025-01-15T10:30:45Z",
        "entity_tags": ["name:john", "location:block-d"],
        "language": "en",
        "chunk_index": 3,
        "chunk_text": "first 100 chars for preview..."
    }
}
```

### Org Isolation in Vector Space

Every query MUST be filtered by org_id. This is the vector-layer equivalent of row-level security.

```go
// CORRECT — always filter by org
results, err := ruvector.Search(ctx, SearchParams{
    Vector:    queryEmbedding,
    TopK:      20,
    Filter:    Filter{OrgID: orgIDFromJWT},
})

// WRONG — never query without org filter
results, err := ruvector.Search(ctx, SearchParams{
    Vector:    queryEmbedding,
    TopK:      20,
    // Missing org filter = security violation
})
```

### Deployment

Ruvector runs as a containerized service on GKE:

```bash
# After studying the repo, deploy based on its documented deployment method
# Typical pattern:
kubectl create namespace ruvector
kubectl apply -f ruvector-deployment.yaml -n ruvector
```

Persistent storage via GKE persistent volumes. Backup via volume snapshots.

### Operations Used by CIE

1. **Store**: After embedding generation, store chunk + metadata
2. **Search**: Semantic similarity search with org_id filter
3. **Cross-call linking**: Search for similar chunks within same org, threshold filtering
4. **Delete**: When tenant data is purged (retention policy)
5. **Partition/namespace management**: Per-org isolation

### Embedding Model Selection

The embedding model must match what Ruvector expects. After studying the repo:
- Determine supported embedding dimensions
- Determine recommended embedding model
- If flexible, use `text-embedding-3-small` (1536 dims) or whatever Ruvector recommends

### Integration Testing

```go
//go:build integration

func TestRuvectorStore_And_Search(t *testing.T) {
    // Store a chunk
    // Search for it
    // Verify org isolation (store under org A, search under org B = no results)
}
```

### Performance Considerations

- Batch embedding storage when processing a single call's chunks
- Use approximate nearest neighbor for search (not exact)
- Monitor query latency — target < 200ms for search
- Scale Ruvector replicas based on query volume
