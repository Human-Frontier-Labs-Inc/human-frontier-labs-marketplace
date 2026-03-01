# Installation Guide

Step-by-step installation for the Chuqlab CSS Theme plugin.

## Prerequisites

- Claude Code CLI installed
- A project using Tailwind CSS v4
- Node.js 18+ (for Tailwind)

## Installation

### Step 1: Install the Plugin

```bash
/plugin marketplace add Human-Frontier-Labs-Inc/human-frontier-labs-marketplace/chuqlab-css-theme
```

Or if you have the marketplace cloned locally:

```bash
/plugin marketplace add ./chuqlab-css-theme
```

### Step 2: Verify Installation

The plugin should now be active. Test it with:

```
"Apply Chuqlab branding to this project"
```

Claude should activate the skill and guide you through applying the theme.

## Manual Setup (Without Plugin)

If you want to apply the theme manually:

### 1. Copy the CSS

Copy `assets/globals.css` to your project's CSS entry point:

- **Next.js**: `app/globals.css`
- **Vite/React**: `src/index.css`
- **Plain HTML**: `styles/globals.css`

### 2. Install Geist Fonts

```bash
npm install geist
```

### 3. Configure Font Variables (Next.js)

In your root layout:

```tsx
import { GeistSans } from 'geist/font/sans';
import { GeistMono } from 'geist/font/mono';

export default function RootLayout({ children }) {
  return (
    <html className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
```

### 4. Use Brand Colors

```html
<div class="bg-chuqlab-primary text-white">Primary navy</div>
<div class="bg-chuqlab-secondary text-white">Secondary red</div>
<div class="text-chuqlab-accent">Accent blue</div>
```

## Troubleshooting

### Plugin Not Activating

**Issue**: Plugin doesn't respond to branding requests
**Solution**:
- Check installation: `/plugin list`
- Use explicit keywords: "Apply Chuqlab CSS theme"
- Restart Claude Code

### Colors Not Showing

**Issue**: Tailwind utilities like `bg-chuqlab-primary` don't work
**Solution**:
- Verify Tailwind CSS v4 is installed (v3 uses a different config format)
- Ensure `@theme` block is in your CSS entry point
- Check that the CSS file is imported in your layout

### Font Not Loading

**Issue**: Geist font not rendering
**Solution**:
- Install the geist package: `npm install geist`
- Add font variables to your HTML element
- Check browser dev tools for font loading errors

## Uninstallation

```bash
/plugin marketplace remove chuqlab-css-theme
```
