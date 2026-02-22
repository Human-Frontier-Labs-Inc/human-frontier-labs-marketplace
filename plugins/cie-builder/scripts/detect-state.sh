#!/bin/bash
# CIE Build State Detection
# Run this to determine where the build currently stands

set -e

echo "=== CIE Build State Detection ==="
echo ""

# Check for BUILD_STATE.md
if [ -f "BUILD_STATE.md" ]; then
    echo "✅ BUILD_STATE.md found:"
    echo "---"
    cat BUILD_STATE.md
    echo "---"
    echo ""
else
    echo "❌ No BUILD_STATE.md found"
fi

# Check repo existence
if [ -d ".git" ]; then
    echo "✅ Git repo exists"
    echo "   Latest commits:"
    git log --oneline -5 2>/dev/null || echo "   (no commits yet)"
    echo "   Tags:"
    git tag -l "phase-*" 2>/dev/null || echo "   (no phase tags)"
    echo ""
else
    echo "❌ No git repo — Phase 0 not started"
    exit 0
fi

# Check Go backend
if [ -f "engine/go.mod" ]; then
    echo "✅ Go backend exists"
    cd engine
    echo "   Running tests..."
    go test ./... 2>&1 | tail -5 || echo "   ⚠️  Tests failed or not present"
    cd ..
else
    echo "❌ No Go backend"
fi

# Check TypeScript frontend
if [ -f "ui/package.json" ]; then
    echo "✅ TypeScript frontend exists"
    cd ui
    echo "   Running tests..."
    npm test -- --passWithNoTests 2>&1 | tail -5 || echo "   ⚠️  Tests failed or not present"
    cd ..
else
    echo "❌ No TypeScript frontend"
fi

# Check infrastructure
if [ -d "infra" ]; then
    echo "✅ Infra scripts exist"
    ls infra/*.sh 2>/dev/null || echo "   (no scripts)"
else
    echo "❌ No infra directory"
fi

# Check migrations
if [ -d "engine/migrations" ]; then
    echo "✅ Migrations exist"
    ls engine/migrations/*.sql 2>/dev/null | wc -l | xargs echo "   SQL files:"
else
    echo "❌ No migrations"
fi

# Check Dockerfiles
find . -name "Dockerfile" -not -path "./node_modules/*" 2>/dev/null | while read f; do
    echo "✅ Dockerfile: $f"
done

# Infer phase
echo ""
echo "=== Phase Inference ==="

PHASE=0
[ -f "engine/go.mod" ] && PHASE=0
[ -d "engine/internal/auth" ] && PHASE=0
[ -d "engine/internal/ingest" ] && PHASE=1
[ -d "engine/internal/transcribe" ] && PHASE=2
[ -d "engine/internal/embed" ] && PHASE=3
[ -d "engine/internal/alert" ] && PHASE=4
[ -d "ui/src/app/chat" ] && PHASE=5

echo "Inferred phase: $PHASE (verify against BUILD_STATE.md and git tags)"
echo ""
echo "Next action: Read references/phases.md for Phase $PHASE details"
