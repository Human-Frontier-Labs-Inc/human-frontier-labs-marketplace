# Next.js 15 Patterns - CareBridge

## Critical Changes from Next.js 14

Next.js 15 introduces async Request APIs. Several patterns have changed.

## Async Params (CRITICAL)

### In App Router Pages

**ALL dynamic route params must be awaited**

```typescript
// ❌ WRONG - Next.js 14 pattern (will error in 15)
export default function Page({ params }: { params: { id: string } }) {
  const { id } = params // ERROR!
}

// ✅ CORRECT - Next.js 15 pattern
type Props = {
  params: Promise<{ id: string }>
}

export default async function Page({ params }: Props) {
  const { id } = await params
  // Use id
}
```

### In API Routes

**ALL dynamic route params must be awaited**

```typescript
// ❌ WRONG
export async function GET(
  request: Request,
  { params }: { params: { userId: string } }
) {
  const { userId } = params // ERROR!
}

// ✅ CORRECT
export async function GET(
  request: Request,
  { params }: { params: Promise<{ userId: string }> }
) {
  const { userId } = await params
  // Use userId
}
```

## Async SearchParams

**SearchParams are also async in Next.js 15**

```typescript
// ❌ WRONG
export default function Page({
  searchParams,
}: {
  searchParams: { caseId?: string }
}) {
  const caseId = searchParams.caseId // ERROR!
}

// ✅ CORRECT
type SearchParams = Promise<{ caseId?: string }>

export default async function Page({
  searchParams,
}: {
  searchParams: SearchParams
}) {
  const params = await searchParams
  const caseId = getCaseIdFromParams(params)
}
```

## Server Components vs Client Components

### When to Use Server Components (Default)

Use server components (no `'use client'`) for:
- Pages that fetch data
- Pages that need SEO
- Static content
- Database queries

```typescript
// Server Component (default)
import { createServerClient } from '@/lib/supabase/server'

export default async function DashboardPage() {
  const supabase = await createServerClient()
  const { data } = await supabase.from('cases').select('*')

  return <div>{/* Render data */}</div>
}
```

### When to Use Client Components

Use `'use client'` for:
- Interactive UI (onClick, onChange, etc.)
- React hooks (useState, useEffect, useContext)
- Browser APIs (localStorage, window, etc.)
- Third-party libraries that need client-side

```typescript
'use client'

import { useState } from 'react'

export function InteractiveComponent() {
  const [count, setCount] = useState(0)

  return <button onClick={() => setCount(count + 1)}>{count}</button>
}
```

### Mixing Server and Client

**Pattern**: Server component fetches data, passes to client component

```typescript
// app/page.tsx (Server Component)
import { ClientComponent } from './client-component'

export default async function Page() {
  const data = await fetchData()

  return <ClientComponent data={data} />
}

// client-component.tsx (Client Component)
'use client'

export function ClientComponent({ data }) {
  const [selected, setSelected] = useState(null)

  return (
    <div onClick={() => setSelected(data)}>
      {/* Interactive UI */}
    </div>
  )
}
```

## Metadata API

Use the Metadata API for SEO:

```typescript
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Dashboard | CareBridge',
  description: 'Manage your care cases',
}

export default function Page() {
  return <div>Dashboard</div>
}
```

## Loading and Error States

### Loading States

Create `loading.tsx` next to `page.tsx`:

```typescript
// app/dashboard/loading.tsx
export default function Loading() {
  return <div>Loading dashboard...</div>
}
```

### Error Boundaries

Create `error.tsx` next to `page.tsx`:

```typescript
// app/dashboard/error.tsx
'use client' // Error boundaries must be client components

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div>
      <h2>Something went wrong!</h2>
      <button onClick={reset}>Try again</button>
    </div>
  )
}
```

## Data Fetching Patterns

### Server-Side Fetching (Preferred)

```typescript
// In Server Component
export default async function Page() {
  const supabase = await createServerClient()
  const { data } = await supabase.from('cases').select('*')

  return <CasesList cases={data} />
}
```

### Client-Side Fetching (When Needed)

```typescript
'use client'

import { useEffect, useState } from 'react'

export function ClientDataFetcher() {
  const [data, setData] = useState(null)

  useEffect(() => {
    fetch('/api/data')
      .then((res) => res.json())
      .then(setData)
  }, [])

  if (!data) return <div>Loading...</div>

  return <div>{/* Render data */}</div>
}
```

## Form Actions

Use Server Actions for forms:

```typescript
// app/actions.ts
'use server'

export async function createCase(formData: FormData) {
  const name = formData.get('name')

  const supabase = await createServerClient()
  await supabase.from('cases').insert({ name })

  revalidatePath('/dashboard')
}

// app/page.tsx
import { createCase } from './actions'

export default function Page() {
  return (
    <form action={createCase}>
      <input name="name" />
      <button type="submit">Create</button>
    </form>
  )
}
```

## Common Mistakes

### ❌ Mistake #1: Forgetting 'use client'

```typescript
// WRONG - Will error because useState needs client
import { useState } from 'react'

export function Component() {
  const [count, setCount] = useState(0) // ERROR!
}

// CORRECT
'use client'

import { useState } from 'react'

export function Component() {
  const [count, setCount] = useState(0)
}
```

### ❌ Mistake #2: Not awaiting params

```typescript
// WRONG
export default function Page({ params }) {
  const { id } = params // ERROR in Next.js 15!
}

// CORRECT
export default async function Page({ params }) {
  const { id } = await params
}
```

### ❌ Mistake #3: Using client-side hooks in server components

```typescript
// WRONG
export default function Page() {
  const router = useRouter() // ERROR!
}

// CORRECT - Add 'use client'
'use client'

export default function Page() {
  const router = useRouter()
}
```

### ❌ Mistake #4: Importing server-only code in client components

```typescript
// WRONG - Client component trying to use server-only code
'use client'

import { createServerClient } from '@/lib/supabase/server' // ERROR!

export function Component() {
  const supabase = await createServerClient() // Won't work!
}

// CORRECT - Use Server Action instead
'use client'

import { getData } from './actions'

export function Component() {
  const handleClick = async () => {
    const data = await getData() // Calls server action
  }
}
```

## Environment Variables

### Public vs Private

```typescript
// ✅ Public (available in browser)
const key = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY

// ✅ Private (server-only)
const secret = process.env.STRIPE_SECRET_KEY // Only works in server components/actions
```

### Accessing in Client Components

```typescript
// ❌ WRONG - Private env vars don't work in client
'use client'

const secret = process.env.STRIPE_SECRET_KEY // undefined!

// ✅ CORRECT - Use public env vars
'use client'

const publicKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
```

## Caching

Next.js 15 has granular caching:

```typescript
// Cache indefinitely (static data)
const data = await fetch('https://api.example.com/data', {
  cache: 'force-cache',
})

// Revalidate every hour
const data = await fetch('https://api.example.com/data', {
  next: { revalidate: 3600 },
})

// Never cache (dynamic data)
const data = await fetch('https://api.example.com/data', {
  cache: 'no-store',
})
```

## Route Handlers (API Routes)

```typescript
// app/api/route.ts
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const id = searchParams.get('id')

  return Response.json({ id })
}

export async function POST(request: Request) {
  const body = await request.json()

  return Response.json({ success: true })
}
```

## Dynamic Routes

```typescript
// app/cases/[caseId]/page.tsx
type Props = {
  params: Promise<{ caseId: string }>
}

export default async function CasePage({ params }: Props) {
  const { caseId } = await params

  return <div>Case: {caseId}</div>
}
```

## Middleware

Use for auth checks, redirects, etc.:

```typescript
// middleware.ts
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

const isProtectedRoute = createRouteMatcher([
  '/dashboard(.*)',
  '/cases(.*)',
])

export default clerkMiddleware((auth, req) => {
  if (isProtectedRoute(req)) auth().protect()
})

export const config = {
  matcher: ['/((?!.*\\..*|_next).*)', '/', '/(api|trpc)(.*)'],
}
```
