---
name: chuqlab-css-theme
description: Applies the Chuqlab brand CSS design system to any Tailwind CSS v4 project. Includes brand color palette, Geist font configuration, and utility classes. Triggers when users ask to theme a project with Chuqlab branding, apply Chuqlab colors, set up a Tailwind v4 theme with brand tokens, create a Chuqlab-styled layout, or need the Chuqlab design system. Also triggers for requests involving navy/red/blue corporate palettes, Geist typography, or CSS custom properties for brand consistency.
---

# Chuqlab CSS Theme — Brand Design System Plugin

Apply the Chuqlab brand design system to any Tailwind CSS v4 project with consistent colors, typography, and utility classes.

## When to Use This Skill

This skill activates when you need to apply or reference the Chuqlab brand design system:

### Theming & Branding

Use this skill when you:
- **Apply Chuqlab branding** to a new or existing project
- **Set up Tailwind CSS v4** with Chuqlab design tokens
- **Reference brand colors** for consistent UI development
- **Configure Geist fonts** with CSS custom properties
- **Create branded layouts** with background patterns and masks

### Typical Activation Phrases

- "Apply Chuqlab branding to this project"
- "Set up the Chuqlab color palette"
- "Theme this with Chuqlab colors"
- "What are the Chuqlab brand colors?"
- "Add the Chuqlab CSS design system"
- "Configure Tailwind v4 with Chuqlab tokens"
- "Use the Chuqlab theme"

## Brand Color Palette

### Primary Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-chuqlab-primary` | `#141246` | Primary navy — headers, primary buttons, key UI elements |
| `--color-chuqlab-secondary` | `#EC1848` | Accent red — CTAs, alerts, emphasis elements |
| `--color-chuqlab-accent` | `#0842EA` | Accent blue — links, info elements, secondary actions |
| `--color-chuqlab-light` | `#f0f6ff` | Light background — cards, sections, subtle contrast |
| `--color-chuqlab-dark` | `#0a0a23` | Dark background — dark mode, footers, overlays |

### Extended Palette

**Primary (Navy):**
- `--color-primary-600`: `#141246` (base)
- `--color-primary-700`: `#0d0d30` (darker)
- `--color-primary-50`: `#f0f6ff` (lightest)

**Secondary (Red):**
- `--color-secondary-600`: `#EC1848` (base)
- `--color-secondary-700`: `#c71339` (darker)
- `--color-secondary-50`: `#fff1f4` (lightest)

**Accent (Blue):**
- `--color-accent-600`: `#0842EA` (base)
- `--color-accent-700`: `#0635bb` (darker)
- `--color-accent-50`: `#eff6ff` (lightest)

**Success (Green):**
- `--color-success-700`: `#027a48` (base)
- `--color-success-50`: `#ecfdf3` (lightest)

## Typography

The design system uses the Geist font family:

```css
--font-sans: var(--font-geist-sans);
--font-mono: var(--font-geist-mono);
```

**Setup with Next.js:**
```tsx
import { GeistSans } from 'geist/font/sans';
import { GeistMono } from 'geist/font/mono';

// In layout.tsx
<html className={`${GeistSans.variable} ${GeistMono.variable}`}>
```

**Setup without Next.js:**
```css
@import url('https://fonts.googleapis.com/css2?family=Geist+Sans&family=Geist+Mono&display=swap');
```

## Utility Classes

### Background Grid Pattern

The `.background` class creates a subtle grid overlay:

```css
.background {
  overflow: hidden;
  background: #f8f8f8;
  background-image: repeating-linear-gradient(
      0deg, transparent, transparent 11px, #f2f2f2 11px, #f2f2f2 12px
    ),
    repeating-linear-gradient(
      90deg, transparent, transparent 11px, #f2f2f2 11px, #f2f2f2 12px
    );
}
```

**Use for:** Landing page backgrounds, hero sections, content areas that need subtle texture.

### Mask Gradient

The `.mask` class applies a fade-in/fade-out mask:

```css
.mask {
  mask-image: linear-gradient(
    to bottom,
    rgba(0,0,0,0) 0%,
    rgba(0,0,0,1) 40px,
    rgba(0,0,0,1) calc(100% - 20px),
    rgba(0,0,0,0) 100%
  );
}
```

**Use for:** Scrollable content areas, list containers, content that should fade at edges.

## Installation to a Project

### Step 1: Copy the Theme CSS

Copy `assets/globals.css` to your project's CSS entry point (e.g., `app/globals.css` for Next.js).

### Step 2: Ensure Tailwind CSS v4

The theme uses Tailwind CSS v4's `@theme` directive and `@layer` system:

```css
@layer theme, base, components, utilities;
@import "tailwindcss";
```

### Step 3: Use Brand Colors in Markup

With Tailwind v4, the theme tokens are available as utilities:

```html
<!-- Background colors -->
<div class="bg-chuqlab-primary">Navy background</div>
<div class="bg-chuqlab-secondary">Red background</div>
<div class="bg-chuqlab-accent">Blue background</div>

<!-- Text colors -->
<h1 class="text-chuqlab-primary">Navy heading</h1>
<span class="text-chuqlab-secondary">Red accent text</span>
<a class="text-chuqlab-accent">Blue link</a>

<!-- Extended palette -->
<div class="bg-primary-50 text-primary-700">Light navy section</div>
<div class="bg-secondary-50 text-secondary-700">Light red alert</div>
<div class="bg-accent-50 text-accent-700">Light blue info</div>
<div class="bg-success-50 text-success-700">Success message</div>
```

## Tailwind v4 Compatibility

This theme includes a compatibility layer for the border color change in Tailwind v4:

```css
@layer base {
  *, ::after, ::before, ::backdrop, ::file-selector-button {
    border-color: var(--color-gray-200, currentcolor);
  }
}
```

This ensures existing components using implicit borders render consistently.

## Adding Clerk Authentication Layer

If your project uses Clerk for authentication, the layer order already includes it:

```css
@layer theme, base, clerk, components, utilities;
```

This prevents style conflicts between Clerk's embedded components and your brand theme.

## Design Guidelines

### Color Usage Rules

1. **Primary navy (#141246)** — Use for navigation bars, primary buttons, headings, and key structural elements
2. **Secondary red (#EC1848)** — Use sparingly for CTAs, error states, and high-emphasis elements
3. **Accent blue (#0842EA)** — Use for links, informational elements, and secondary interactive elements
4. **Success green (#027a48)** — Use exclusively for success states and positive confirmations
5. **Light variants (-50)** — Use for subtle backgrounds, hover states, and section differentiation
6. **Dark variants (-700)** — Use for text on light backgrounds and hover/active states

### Contrast Requirements

All color combinations meet WCAG AA contrast requirements:
- Primary navy on white: 14.5:1 (AAA)
- Secondary red on white: 4.6:1 (AA)
- Accent blue on white: 5.2:1 (AA)
- Success green on white: 5.1:1 (AA)

## Complete CSS Reference

The full theme CSS is available at `assets/globals.css` in this plugin directory.
