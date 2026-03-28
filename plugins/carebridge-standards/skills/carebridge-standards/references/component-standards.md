# Component Standards - CareBridge

## Critical Rule: No Custom Components

**NEVER create custom UI components from scratch. ALWAYS use shadcn/ui.**

## Using shadcn/ui

### Adding Components

```bash
# List available components
npx shadcn@latest add

# Add a specific component
npx shadcn@latest add button
npx shadcn@latest add card
npx shadcn@latest add dialog
npx shadcn@latest add form
```

This adds components to `src/components/ui/` with proper TypeScript types and styling.

### Example: Adding a Button

```bash
npx shadcn@latest add button
```

Then use it:

```typescript
import { Button } from '@/components/ui/button'

export function MyComponent() {
  return <Button variant="default">Click me</Button>
}
```

### Available Variants

shadcn components come with built-in variants. Check the component file for options:

```typescript
// Button variants
<Button variant="default">Default</Button>
<Button variant="destructive">Delete</Button>
<Button variant="outline">Outline</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="link">Link</Button>

// Card components
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>
    Content here
  </CardContent>
  <CardFooter>
    Footer actions
  </CardFooter>
</Card>
```

## Component Organization

### Location

```
src/
├── components/
│   ├── ui/              # shadcn components (DON'T EDIT)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   └── ...
│   ├── dashboard/       # Dashboard-specific components
│   ├── calendar/        # Calendar-specific components
│   ├── concierge/       # Concierge-specific components
│   └── nav-main.tsx     # Global navigation components
```

### Naming Conventions

- UI components: `kebab-case.tsx` (button.tsx, card.tsx)
- Feature components: `PascalCase.tsx` (DashboardHeader.tsx, CaseList.tsx)
- Use descriptive names: `ConciergeBookingForm.tsx` not `Form.tsx`

## Styling Rules

### CSS Variables (READ-ONLY)

**NEVER create custom CSS variables. ONLY use existing ones from `globals.css`.**

Available CSS variables:

```css
/* From globals.css */
--background
--foreground
--card
--card-foreground
--popover
--popover-foreground
--primary
--primary-foreground
--secondary
--secondary-foreground
--muted
--muted-foreground
--accent
--accent-foreground
--destructive
--destructive-foreground
--border
--input
--ring
```

### Using CSS Variables

```typescript
// ✅ CORRECT - Use existing variables
<div className="bg-background text-foreground">
  Content
</div>

// ✅ CORRECT - Use Tailwind utility classes
<div className="bg-primary text-primary-foreground rounded-lg p-4">
  Card content
</div>

// ❌ WRONG - Custom CSS variables
<div style={{ backgroundColor: 'var(--my-custom-color)' }}>
  Content
</div>

// ❌ WRONG - Inline styles
<div style={{ backgroundColor: '#3498db', padding: '16px' }}>
  Content
</div>
```

### Tailwind Classes

Use Tailwind utility classes for styling:

```typescript
// ✅ CORRECT
<div className="flex items-center gap-4 p-6 rounded-lg border">
  <div className="flex-1">Content</div>
  <Button variant="default">Action</Button>
</div>

// ❌ WRONG - Custom CSS classes
<div className="my-custom-container">
  Content
</div>
```

## Form Components

### Using React Hook Form + Zod

CareBridge uses React Hook Form with Zod validation:

```typescript
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

const formSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email'),
})

export function MyForm() {
  const form = useForm({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      email: '',
    },
  })

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    // Handle submission
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit">Submit</Button>
      </form>
    </Form>
  )
}
```

## Dialog/Modal Pattern

```typescript
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

export function MyDialog() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Open Dialog</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Dialog Title</DialogTitle>
        </DialogHeader>
        <div>Dialog content here</div>
      </DialogContent>
    </Dialog>
  )
}
```

## Empty States Pattern

Use the `EmptyState` component for "no data" scenarios:

```typescript
import { EmptyState } from '@/components/dashboard/empty-state'
import { Users } from 'lucide-react'

export function MyComponent({ data }) {
  if (!data || data.length === 0) {
    return (
      <EmptyState
        icon={Users}
        title="No Cases Found"
        description="Create your first care case to get started"
      />
    )
  }

  return <div>{/* Render data */}</div>
}
```

## Loading States

```typescript
import { Skeleton } from '@/components/ui/skeleton'

export function LoadingState() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-12 w-full" />
      <Skeleton className="h-12 w-full" />
      <Skeleton className="h-12 w-full" />
    </div>
  )
}
```

## Icons

Use Lucide React for icons:

```typescript
import { Calendar, User, Settings, CreditCard } from 'lucide-react'

export function MyComponent() {
  return (
    <div className="flex items-center gap-2">
      <Calendar className="h-4 w-4" />
      <span>Calendar</span>
    </div>
  )
}
```

## Common Component Patterns

### Card with Actions

```typescript
<Card>
  <CardHeader>
    <div className="flex items-center justify-between">
      <CardTitle>Title</CardTitle>
      <Button variant="ghost" size="sm">
        <Settings className="h-4 w-4" />
      </Button>
    </div>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>
    Content here
  </CardContent>
  <CardFooter className="flex justify-end gap-2">
    <Button variant="outline">Cancel</Button>
    <Button>Save</Button>
  </CardFooter>
</Card>
```

### List with Items

```typescript
<div className="space-y-2">
  {items.map((item) => (
    <Card key={item.id}>
      <CardContent className="flex items-center justify-between p-4">
        <div>
          <h3 className="font-medium">{item.title}</h3>
          <p className="text-sm text-muted-foreground">{item.description}</p>
        </div>
        <Button variant="ghost" size="sm">
          View
        </Button>
      </CardContent>
    </Card>
  ))}
</div>
```

## Responsive Design

Use Tailwind responsive prefixes:

```typescript
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* Responsive grid */}
</div>

<div className="flex flex-col sm:flex-row gap-4">
  {/* Stack vertically on mobile, horizontally on larger screens */}
</div>
```

## Common Mistakes

### ❌ Mistake #1: Creating custom components

```typescript
// WRONG - Don't create custom buttons
export function CustomButton({ children }) {
  return (
    <button className="custom-btn">
      {children}
    </button>
  )
}

// CORRECT - Use shadcn button
import { Button } from '@/components/ui/button'

<Button variant="default">{children}</Button>
```

### ❌ Mistake #2: Custom CSS variables

```typescript
// WRONG - Don't create custom variables
<div style={{ color: 'var(--my-custom-color)' }}>
  Content
</div>

// CORRECT - Use existing variables
<div className="text-primary">
  Content
</div>
```

### ❌ Mistake #3: Inline styles

```typescript
// WRONG - Avoid inline styles
<div style={{ padding: '16px', margin: '8px' }}>
  Content
</div>

// CORRECT - Use Tailwind classes
<div className="p-4 m-2">
  Content
</div>
```

### ❌ Mistake #4: Not using TypeScript types

```typescript
// WRONG - No types
export function MyComponent({ user }) {
  return <div>{user.name}</div>
}

// CORRECT - Proper TypeScript types
type Props = {
  user: {
    name: string
    email: string
  }
}

export function MyComponent({ user }: Props) {
  return <div>{user.name}</div>
}
```

## Component Checklist

Before creating a component:

- [ ] Is there a shadcn component for this? (Use `npx shadcn@latest add`)
- [ ] Am I using existing CSS variables?
- [ ] Am I using Tailwind classes instead of inline styles?
- [ ] Do I have proper TypeScript types?
- [ ] Is the component in the right directory?
- [ ] Am I preserving case context in navigation?
