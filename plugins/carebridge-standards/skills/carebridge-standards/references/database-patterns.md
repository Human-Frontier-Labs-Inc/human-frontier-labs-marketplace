# Database Patterns - CareBridge

## Overview

CareBridge uses Supabase (PostgreSQL) for data storage. Security is enforced via **Clerk authentication + Server Actions** for most tables, with RLS enabled only for specific tables (user_profiles, consultations, subscriptions).

## Database Schema Reference

### Auto-Generated Types (Single Source of Truth)

The complete database schema is auto-generated in **`src/lib/database.types.ts`**.

**To regenerate types after migrations:**

```bash
# From linked remote project (recommended)
npx supabase gen types typescript --linked > src/lib/database.types.ts

# From local dev database
npx supabase gen types typescript --local > src/lib/database.types.ts

# From specific project ID
npx supabase gen types typescript --project-id YOUR_PROJECT_ID > src/lib/database.types.ts
```

**ALWAYS regenerate types after creating migrations!**

## Supabase Client Patterns

### Server-Side Client (Preferred)

Use in Server Components and Server Actions:

```typescript
import { createServerClient } from '@/lib/supabase/server'

export default async function Page() {
  const supabase = await createServerClient()

  const { data, error } = await supabase
    .from('cases')
    .select('*')
    .eq('owner_id', userId)

  if (error) {
    console.error('Database error:', error)
    return <ErrorDisplay />
  }

  return <CasesList cases={data} />
}
```

### Client-Side Client (When Needed)

Use in Client Components:

```typescript
'use client'

import { createBrowserClient } from '@/lib/supabase/client'
import { useEffect, useState } from 'react'

export function ClientComponent() {
  const [data, setData] = useState(null)
  const supabase = createBrowserClient()

  useEffect(() => {
    async function fetchData() {
      const { data } = await supabase.from('cases').select('*')
      setData(data)
    }
    fetchData()
  }, [])

  // ...
}
```

## Migrations

### Creating Migrations

**ALWAYS use Supabase CLI for schema changes:**

```bash
# Create a new migration
npx supabase migration new migration_name

# This creates: supabase/migrations/YYYYMMDD_migration_name.sql
```

### Migration Structure

```sql
-- Migration: 20251018_add_concierge_packages.sql

-- Create table
CREATE TABLE IF NOT EXISTS concierge_packages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_user_id TEXT NOT NULL,
  package_type VARCHAR(50) NOT NULL,
  price_paid_cents INT NOT NULL CHECK (price_paid_cents > 0),
  status VARCHAR(20) DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes
CREATE INDEX idx_concierge_packages_user
  ON concierge_packages(clerk_user_id);

CREATE INDEX idx_concierge_packages_status
  ON concierge_packages(status);

-- Add table comment
COMMENT ON TABLE concierge_packages IS 'Stores concierge service package purchases. Security enforced by Clerk auth + Server Actions (RLS disabled)';

-- Create trigger for updated_at (if function exists)
CREATE TRIGGER update_concierge_packages_updated_at
  BEFORE UPDATE ON concierge_packages
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Add column comments
COMMENT ON COLUMN concierge_packages.price_paid_cents IS 'Price paid in cents (e.g., 39900 = $399.00)';
```

### Applying Migrations

```bash
# Apply locally
npx supabase db reset

# Apply to remote (production)
npx supabase db push
```

## Security Architecture

### CareBridge Uses Two Security Patterns:

**Pattern 1: Clerk Authentication + Server Actions (Most Tables)**

Most tables have RLS **disabled** and rely on:
- Clerk authentication for user identity
- Server Actions that enforce authorization logic
- Server-side validation before database operations

```sql
-- Example: Most tables use this pattern
CREATE TABLE cases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id TEXT NOT NULL,
  -- ... other columns
);

-- RLS is DISABLED - security enforced in Server Actions
COMMENT ON TABLE cases IS 'Security enforced by Clerk auth + Server Actions (RLS disabled)';
```

**Pattern 2: Row-Level Security (Specific Tables Only)**

Only 3 tables use RLS:
- `user_profiles` - User profile data
- `consultations` - Consultation bookings
- `subscriptions` - Subscription data

```sql
-- Example: Tables with RLS enabled
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_own_profile"
  ON user_profiles
  FOR ALL
  USING (auth.jwt() ->> 'sub' = clerk_user_id);
```

### When to Use Each Pattern

**Use Clerk + Server Actions (default):**
- Complex authorization logic (team access, roles)
- Multi-table operations requiring consistency
- Business logic validation
- Most application features

**Use RLS (rare):**
- Simple user-owned resources
- Direct client queries (rare in Next.js)
- Additional security layer for sensitive data

### Server Action Security Pattern

```typescript
// src/lib/actions/case-actions.ts
'use server'

import { auth } from '@clerk/nextjs/server'
import { createServerClient } from '@/lib/supabase/server'

export async function getCases() {
  const { userId } = await auth()

  if (!userId) {
    throw new Error('Unauthorized')
  }

  const supabase = await createServerClient()

  // Security: Only fetch cases owned by authenticated user
  const { data, error } = await supabase
    .from('cases')
    .select('*')
    .eq('owner_id', userId)

  if (error) throw error
  return data
}
```

## Query Patterns

### Basic CRUD

```typescript
// Create
const { data, error } = await supabase
  .from('cases')
  .insert({
    owner_id: userId,
    care_recipient_name: 'John Doe',
  })
  .select()
  .single()

// Read (single)
const { data, error } = await supabase
  .from('cases')
  .select('*')
  .eq('id', caseId)
  .single()

// Read (multiple)
const { data, error } = await supabase
  .from('cases')
  .select('*')
  .eq('owner_id', userId)

// Update
const { data, error } = await supabase
  .from('cases')
  .update({ care_recipient_name: 'Jane Doe' })
  .eq('id', caseId)

// Delete
const { data, error } = await supabase
  .from('cases')
  .delete()
  .eq('id', caseId)
```

### Joins (Relations)

```typescript
// Get cases with their members
const { data, error } = await supabase
  .from('cases')
  .select(`
    *,
    case_members (
      id,
      user_id,
      role
    )
  `)
  .eq('owner_id', userId)
```

### Filtering

```typescript
// Equals
.eq('status', 'active')

// Not equals
.neq('status', 'deleted')

// Greater than
.gt('created_at', '2024-01-01')

// In array
.in('status', ['active', 'pending'])

// Is null
.is('deleted_at', null)

// Like (case-insensitive)
.ilike('name', '%john%')

// Order
.order('created_at', { ascending: false })

// Limit
.limit(10)

// Range (pagination)
.range(0, 9) // First 10 items
```

### Counting

```typescript
const { count, error } = await supabase
  .from('cases')
  .select('*', { count: 'exact', head: true })
  .eq('owner_id', userId)
```

### Upsert (Insert or Update)

```typescript
const { data, error } = await supabase
  .from('subscriptions')
  .upsert({
    clerk_user_id: userId,
    is_active: true,
  })
  .select()
```

## Transaction Patterns

### Using RPC for Transactions

Create a database function:

```sql
-- supabase/migrations/20251018_create_case_with_member.sql
CREATE OR REPLACE FUNCTION create_case_with_member(
  p_owner_id TEXT,
  p_case_name TEXT
) RETURNS UUID AS $$
DECLARE
  v_case_id UUID;
BEGIN
  -- Insert case
  INSERT INTO cases (owner_id, care_recipient_name)
  VALUES (p_owner_id, p_case_name)
  RETURNING id INTO v_case_id;

  -- Insert owner as member
  INSERT INTO case_members (case_id, user_id, role)
  VALUES (v_case_id, p_owner_id, 'owner');

  RETURN v_case_id;
END;
$$ LANGUAGE plpgsql;
```

Call from TypeScript:

```typescript
const { data, error } = await supabase.rpc('create_case_with_member', {
  p_owner_id: userId,
  p_case_name: 'John Doe',
})
```

## Error Handling

```typescript
const { data, error } = await supabase
  .from('cases')
  .select('*')
  .eq('id', caseId)
  .single()

if (error) {
  console.error('Database error:', error)

  // Check for specific error codes
  if (error.code === 'PGRST116') {
    // Not found
    return { error: 'Case not found' }
  }

  return { error: 'Failed to fetch case' }
}

return { data }
```

## Type Safety with Auto-Generated Types

CareBridge uses auto-generated types from `src/lib/database.types.ts`:

```typescript
import { Database } from '@/lib/database.types'

// Extract table types
type Case = Database['public']['Tables']['cases']['Row']
type CaseInsert = Database['public']['Tables']['cases']['Insert']
type CaseUpdate = Database['public']['Tables']['cases']['Update']

// Use with Supabase client
const supabase = createServerClient<Database>()

// Typed queries
const { data, error } = await supabase
  .from('cases') // ✅ Autocomplete for table names
  .select('*')   // ✅ Typed return value
  .eq('id', caseId)
```

**Remember to regenerate types after migrations:**

```bash
npx supabase gen types typescript --linked > src/lib/database.types.ts
```

## Realtime Subscriptions

```typescript
'use client'

import { useEffect } from 'react'
import { createBrowserClient } from '@/lib/supabase/client'

export function RealtimeComponent() {
  const supabase = createBrowserClient()

  useEffect(() => {
    const channel = supabase
      .channel('cases-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'cases',
        },
        (payload) => {
          console.log('Change received!', payload)
          // Update UI
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [])

  return <div>Listening for changes...</div>
}
```

## Common Mistakes

### ❌ Mistake #1: Not checking for errors

```typescript
// WRONG - No error handling
const { data } = await supabase.from('cases').select('*')
return data // Could be null!

// CORRECT
const { data, error } = await supabase.from('cases').select('*')

if (error) {
  console.error('Error:', error)
  return { error: error.message }
}

return { data }
```

### ❌ Mistake #2: Using client in server components

```typescript
// WRONG - Don't import client in server components
import { createBrowserClient } from '@/lib/supabase/client'

export default async function Page() {
  const supabase = createBrowserClient() // ERROR!
}

// CORRECT - Use server client
import { createServerClient } from '@/lib/supabase/server'

export default async function Page() {
  const supabase = await createServerClient()
}
```

### ❌ Mistake #3: Not securing Server Actions

```typescript
// WRONG - No authentication check
'use server'

export async function deleteCase(caseId: string) {
  const supabase = await createServerClient()
  await supabase.from('cases').delete().eq('id', caseId)
  // Anyone can delete any case!
}

// CORRECT - Verify user owns the case
'use server'

import { auth } from '@clerk/nextjs/server'

export async function deleteCase(caseId: string) {
  const { userId } = await auth()

  if (!userId) {
    throw new Error('Unauthorized')
  }

  const supabase = await createServerClient()

  // Verify ownership before deleting
  const { data: caseData } = await supabase
    .from('cases')
    .select('owner_id')
    .eq('id', caseId)
    .single()

  if (caseData?.owner_id !== userId) {
    throw new Error('Unauthorized')
  }

  await supabase.from('cases').delete().eq('id', caseId)
}
```

### ❌ Mistake #4: Not using indexes

```sql
-- WRONG - Frequently queried column without index
CREATE TABLE cases (
  id UUID PRIMARY KEY,
  owner_id TEXT NOT NULL -- No index!
);

-- CORRECT - Add indexes for frequently queried columns
CREATE TABLE cases (
  id UUID PRIMARY KEY,
  owner_id TEXT NOT NULL
);

CREATE INDEX idx_cases_owner ON cases(owner_id);
```

### ❌ Mistake #5: Not using migrations

```typescript
// WRONG - Creating tables via SQL in application code
await supabase.sql`CREATE TABLE ...` // Don't do this!

// CORRECT - Use migrations
// Create: supabase/migrations/20251018_create_table.sql
// Then run: npx supabase db push
```

## Performance Tips

1. **Use indexes** for frequently queried columns
2. **Select specific columns** instead of `select('*')`
3. **Use pagination** with `.range()` for large datasets
4. **Batch operations** when possible
5. **Use RPC functions** for complex operations
6. **Cache results** when appropriate

## Migration Checklist

When creating a migration:

- [ ] Use `npx supabase migration new name`
- [ ] Include `IF NOT EXISTS` clauses
- [ ] Add appropriate indexes for frequently queried columns
- [ ] Add table comment indicating security pattern (RLS vs Clerk + Server Actions)
- [ ] Only enable RLS if needed (most tables use Clerk + Server Actions)
- [ ] Add `updated_at` trigger if needed
- [ ] Add column comments for documentation
- [ ] Test locally with `npx supabase db reset`
- [ ] Push to production with `npx supabase db push`
- [ ] **Regenerate TypeScript types:** `npx supabase gen types typescript --linked > src/lib/database.types.ts`
