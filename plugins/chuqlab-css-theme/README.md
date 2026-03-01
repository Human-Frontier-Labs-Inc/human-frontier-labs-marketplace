# Chuqlab CSS Theme

Apply the Chuqlab brand design system to any Tailwind CSS v4 project with consistent colors, typography, and utility classes.

## What It Does

This plugin provides:

1. **Brand color palette** — Navy primary, red secondary, blue accent with full shade ranges
2. **Typography config** — Geist Sans and Geist Mono font setup
3. **Tailwind v4 theme** — Native `@theme` directive with CSS custom properties
4. **Utility classes** — Grid background pattern and mask gradient helpers
5. **Design guidelines** — Color usage rules and WCAG contrast compliance

## Brand Colors

| Color | Hex | Preview |
|-------|-----|---------|
| Primary Navy | `#141246` | Headings, primary buttons, navigation |
| Secondary Red | `#EC1848` | CTAs, alerts, emphasis |
| Accent Blue | `#0842EA` | Links, info elements |
| Light | `#f0f6ff` | Subtle backgrounds |
| Dark | `#0a0a23` | Dark mode, footers |

## Installation

```bash
/plugin marketplace add Human-Frontier-Labs-Inc/human-frontier-labs-marketplace/chuqlab-css-theme
```

## Quick Start

Ask Claude Code to apply the theme:

```
"Apply Chuqlab branding to this project"
```

The skill will:
- Copy the theme CSS to your project
- Configure Tailwind v4 with brand tokens
- Guide color and typography usage

## Usage Examples

### Apply Full Theme
```
"Set up my Next.js app with the Chuqlab design system"
```

### Reference Colors
```
"What are the Chuqlab brand colors?"
```

### Add to Existing Project
```
"Add Chuqlab theme tokens to my existing Tailwind config"
```

## Tailwind v4 Utilities

Once installed, use brand colors directly in markup:

```html
<div class="bg-chuqlab-primary text-white">Navy section</div>
<button class="bg-chuqlab-secondary text-white">Red CTA</button>
<a class="text-chuqlab-accent hover:text-accent-700">Blue link</a>
```

## Requirements

- Tailwind CSS v4+
- CSS custom properties support (all modern browsers)
- Geist font package (for typography)
