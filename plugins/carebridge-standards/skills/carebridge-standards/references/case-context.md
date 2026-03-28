# Case Context Management - CareBridge

## Overview

CareBridge is a multi-case management system where users can manage multiple care recipients. The `caseId` is the primary context identifier that must be preserved across ALL navigation.

## Critical Rule

**NEVER navigate to a page without preserving the current `caseId`.**

## How Case Context Works

### URL Structure

All protected routes must support the `caseId` query parameter:

```
/dashboard?caseId=uuid-here
/calendar?caseId=uuid-here
/subscriptions?caseId=uuid-here
/case-settings?caseId=uuid-here
```

### Reading Case Context

Use the helper function to safely extract `caseId`:

```typescript
// In Server Components (pages)
import { getCaseIdFromParams } from '@/lib/case-context'

type SearchParams = Promise<{ caseId?: string }>

export default async function MyPage({
  searchParams,
}: {
  searchParams: SearchParams
}) {
  const params = await searchParams // Next.js 15 requirement
  const caseId = getCaseIdFromParams(params)

  if (!caseId) {
    // Show "No case selected" empty state
    return <EmptyState />
  }

  // Use caseId for data fetching
  const data = await getData(caseId)
  // ...
}
```

```typescript
// In Client Components
'use client'

import { useSearchParams } from 'next/navigation'
import { useState, useEffect } from 'react'

export function MyClientComponent() {
  const searchParams = useSearchParams()
  const [caseId, setCaseId] = useState<string | null>(null)

  // Prevent hydration mismatch
  useEffect(() => {
    setCaseId(searchParams.get('caseId'))
  }, [searchParams])

  if (!caseId) return null

  // Use caseId
}
```

### Preserving Case Context in Navigation

**All navigation links MUST preserve caseId:**

```typescript
// ✅ CORRECT - Preserves caseId
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'

const searchParams = useSearchParams()
const caseId = searchParams.get('caseId')

<Link href={caseId ? `/dashboard?caseId=${caseId}` : '/dashboard'}>
  Dashboard
</Link>

// ❌ WRONG - Loses case context
<Link href="/dashboard">
  Dashboard
</Link>
```

### Navigation Component Pattern

See `src/components/nav-main.tsx` for the correct pattern:

```typescript
'use client'

export function NavMain({ items }) {
  const searchParams = useSearchParams()
  const [caseId, setCaseId] = useState<string | null>(null)

  useEffect(() => {
    setCaseId(searchParams.get('caseId'))
  }, [searchParams])

  return items.map((item) => {
    // Preserve caseId in ALL navigation
    const url = caseId ? `${item.url}?caseId=${caseId}` : item.url

    return <Link href={url}>{item.title}</Link>
  })
}
```

## Case Switching

Case switching happens in the sidebar via `CaseSwitcher` component. When a user selects a different case:

1. The URL updates with the new `caseId`
2. All navigation automatically preserves the new `caseId`
3. The page re-renders with new case data

## Empty States

When `caseId` is missing, show a helpful empty state:

```typescript
if (!caseId) {
  return (
    <EmptyState
      icon={Users}
      title="No Case Selected"
      description="Select a case from the sidebar to continue"
    />
  )
}
```

## Common Mistakes

### ❌ Mistake #1: Forgetting to preserve caseId in links

```typescript
// WRONG - Will break case context
<Link href="/subscriptions">Subscribe</Link>
```

### ❌ Mistake #2: Not handling Next.js 15 async params

```typescript
// WRONG - In Next.js 15, params are async
export default function Page({ searchParams }) {
  const caseId = searchParams.caseId // ERROR!
}

// CORRECT
export default async function Page({ searchParams }) {
  const params = await searchParams
  const caseId = getCaseIdFromParams(params)
}
```

### ❌ Mistake #3: Using router.push without caseId

```typescript
// WRONG
router.push('/dashboard')

// CORRECT
const caseId = searchParams.get('caseId')
router.push(caseId ? `/dashboard?caseId=${caseId}` : '/dashboard')
```

## Testing Case Context

When testing a feature:

1. Navigate to a page with a caseId
2. Click any link/button that navigates
3. Verify the URL still has `?caseId=...`
4. Repeat for all navigation paths

If caseId is lost, you'll see the "No Case Selected" empty state - this indicates broken context preservation.
