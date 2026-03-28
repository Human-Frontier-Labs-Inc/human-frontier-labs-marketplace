# Stripe Integration - CareBridge

## Overview

CareBridge uses Stripe for:
- **SaaS Subscription**: $19.99/month platform access
- **Concierge Packages**: 4 service packages (Essentials, Benefits, Concierge Plus, White-Glove)

## Architecture

### Pricing Configuration (Single Source of Truth)

**ALL pricing lives in `src/lib/config/concierge-pricing.ts`**

```typescript
export const CONCIERGE_PACKAGES: Record<PackageType, ConciergePackage> = {
  essentials: {
    name: 'Essentials Package',
    priceRange: '$399 – $899',
    payment_type: 'one_time',
    pricing: {
      type: 'range',      // Allows any price in range
      min: 39900,         // $399 in cents
      max: 89900          // $899 in cents
    }
  },
  concierge_plus: {
    name: 'Concierge Plus',
    priceRange: '$249 – $499/month',
    payment_type: 'subscription',
    pricing: {
      type: 'tiers',      // Predefined Stripe price IDs
      tiers: [
        {
          name: 'Light Support',
          price: 24900,
          priceId: process.env.NEXT_PUBLIC_STRIPE_CONCIERGE_PLUS_LIGHT_PRICE_ID,
        },
        // ... more tiers
      ]
    }
  }
}
```

### Flexible Pricing System

CareBridge supports two pricing approaches:

1. **Tiered Pricing** (Concierge Plus, White-Glove)
   - Predefined Stripe price IDs
   - User selects from available tiers
   - Uses Stripe's price objects

2. **Range Pricing** (Essentials, Benefits)
   - Custom pricing within a range
   - Uses Stripe `price_data` for dynamic pricing
   - Staff can set exact price during booking

## Stripe Product Setup

### Automated Setup Script

```bash
cd scripts
./setup-carebridge-pricing.sh
```

This creates:
- SaaS subscription product ($19.99/mo)
- Concierge Plus tiers (3 prices)
- White-Glove tiers (3 prices)
- Test customer
- Generates .env.stripe with all IDs

### Environment Variables

Required in `.env.local`:

```bash
# Stripe Keys
STRIPE_SECRET_KEY=sk_test_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# SaaS Subscription
NEXT_PUBLIC_STRIPE_SAAS_MONTHLY_PRICE_ID=price_...

# Concierge Plus Tiers
NEXT_PUBLIC_STRIPE_CONCIERGE_PLUS_LIGHT_PRICE_ID=price_...
NEXT_PUBLIC_STRIPE_CONCIERGE_PLUS_STANDARD_PRICE_ID=price_...
NEXT_PUBLIC_STRIPE_CONCIERGE_PLUS_PREMIUM_PRICE_ID=price_...

# White-Glove Tiers
NEXT_PUBLIC_STRIPE_WHITE_GLOVE_STANDARD_PRICE_ID=price_...
NEXT_PUBLIC_STRIPE_WHITE_GLOVE_PREMIUM_PRICE_ID=price_...
NEXT_PUBLIC_STRIPE_WHITE_GLOVE_ENTERPRISE_PRICE_ID=price_...
```

## Creating Checkout Sessions

### SaaS Subscription

```typescript
// Fixed price - no user input needed
const response = await fetch('/api/create-subscription-checkout', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ caseId }), // Preserve case context
})
```

API route automatically uses the SaaS price ID from env vars.

### Concierge Packages

```typescript
import { createConciergeCheckout } from '@/lib/actions/concierge-actions'

// For tiered pricing (Concierge Plus, White-Glove)
const result = await createConciergeCheckout({
  package_type: 'concierge_plus',
  price_cents: 24900, // Must match a tier price
  display_name: 'Light Support',
  case_id: caseId,
})

// For range pricing (Essentials, Benefits)
const result = await createConciergeCheckout({
  package_type: 'essentials',
  price_cents: 50000, // Any value between min/max
  display_name: 'Essentials Package',
  case_id: caseId,
})
```

The action automatically:
- Validates price is within allowed range/tiers
- Creates Stripe checkout with correct mode (subscription vs payment)
- Adds metadata for webhook routing
- Returns checkout URL

## Webhook Handling

**File**: `src/app/api/webhooks/stripe/route.ts`

### Metadata-Driven Routing

Webhooks determine the type by checking `session.metadata.package_type`:

```typescript
case 'checkout.session.completed': {
  if (session.metadata?.package_type) {
    // Concierge package purchase
    await handleConciergeCheckout(session)
  } else if (session.subscription) {
    // SaaS subscription
    await handleSaaSSubscriptionCheckout(session)
  }
  break
}
```

### Required Metadata

Always include in checkout sessions:

```typescript
metadata: {
  clerk_user_id: userId,
  package_type: 'concierge_plus',  // For concierge packages
  payment_type: 'subscription',     // one_time, project_based, or subscription
  price_display_name: 'Light Support',
}
```

### Webhook Events

Handle these events:

- `checkout.session.completed` - Create subscription/package record
- `customer.subscription.updated` - Update subscription status
- `customer.subscription.deleted` - Mark as cancelled

## Database Structure

### SaaS Subscriptions

Table: `subscriptions`

```sql
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY,
  clerk_user_id TEXT NOT NULL,
  stripe_subscription_id VARCHAR(255),
  is_active BOOLEAN DEFAULT false,  -- Simple boolean, no tiers
  status VARCHAR(50),
  current_period_end TIMESTAMPTZ,
  -- ...
)
```

### Concierge Packages

Table: `concierge_packages`

```sql
CREATE TABLE concierge_packages (
  id UUID PRIMARY KEY,
  clerk_user_id TEXT NOT NULL,
  package_type VARCHAR(50) NOT NULL,     -- essentials, benefits, etc.
  payment_type VARCHAR(20) NOT NULL,     -- one_time, project_based, subscription
  stripe_payment_intent_id VARCHAR(255), -- For one-time
  stripe_subscription_id VARCHAR(255),   -- For subscriptions
  price_paid_cents INT NOT NULL,
  price_display_name VARCHAR(100),
  status VARCHAR(20) DEFAULT 'pending',
  -- ...
)
```

## Testing

### Local Webhook Testing

```bash
# Terminal 1: Start webhook listener
stripe listen --forward-to localhost:3000/api/webhooks/stripe

# Copy the webhook secret (whsec_...) to .env.local as STRIPE_WEBHOOK_SECRET

# Terminal 2: Start dev server
npm run dev
```

### Test Cards

- Success: `4242 4242 4242 4242`
- Requires Auth: `4000 0025 0000 3155`
- Declined: `4000 0000 0000 9995`

Expiry: Any future date | CVC: Any 3 digits | ZIP: Any 5 digits

### Testing Checklist

1. ✅ SaaS subscription checkout
2. ✅ Concierge package with tiers
3. ✅ Concierge package with custom price
4. ✅ Webhook creates database records
5. ✅ Success page displays correctly
6. ✅ Billing page shows all subscriptions

## Common Mistakes

### ❌ Mistake #1: Not validating price

```typescript
// WRONG - No validation
await createConciergeCheckout({
  price_cents: 1000000, // Way above max!
})

// CORRECT - Use the action, it validates automatically
const result = await createConciergeCheckout({
  package_type: 'essentials',
  price_cents: 50000,
  display_name: 'Essentials',
})

if (!result.success) {
  // Handle validation error
}
```

### ❌ Mistake #2: Hardcoding price IDs

```typescript
// WRONG - Hardcoded
const priceId = 'price_abc123'

// CORRECT - Use env vars
const priceId = process.env.NEXT_PUBLIC_STRIPE_SAAS_MONTHLY_PRICE_ID
```

### ❌ Mistake #3: Not including metadata

```typescript
// WRONG - Webhook won't know how to route
const session = await stripe.checkout.sessions.create({
  line_items: [...],
  mode: 'subscription',
})

// CORRECT - Include routing metadata
const session = await stripe.checkout.sessions.create({
  line_items: [...],
  mode: 'subscription',
  metadata: {
    clerk_user_id: userId,
    package_type: 'concierge_plus',
    payment_type: 'subscription',
  },
})
```

### ❌ Mistake #4: Forgetting to await Stripe responses

```typescript
// WRONG - Missing await
const session = stripe.checkout.sessions.create({...})

// CORRECT
const session = await stripe.checkout.sessions.create({...})
```

## Changing Pricing

To change pricing (add tiers, adjust prices, etc.):

1. Update `src/lib/config/concierge-pricing.ts`
2. Create new Stripe products/prices
3. Update environment variables
4. No backend code changes needed!

The flexible architecture supports any pricing changes without touching server actions or webhooks.

## Documentation

- `STRIPE-SETUP-GUIDE.md` - Complete setup instructions
- `CAREBRIDGE-PRICING-IMPLEMENTATION.md` - Technical deep dive
- `scripts/README.md` - Script documentation
