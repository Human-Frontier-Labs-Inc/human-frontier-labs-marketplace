# Architecture Decisions

Documentation of key design decisions for the Chuqlab CSS Theme plugin.

## Tailwind CSS v4 Over v3

**Decision**: Use Tailwind CSS v4's native `@theme` directive instead of `tailwind.config.js`
**Rationale**:
- Tailwind v4 is CSS-native — no JavaScript config file needed
- `@theme` directive provides first-class CSS custom property support
- Better performance (no config compilation step)
- Forward-compatible with the Tailwind ecosystem direction

**Trade-offs**:
- Requires Tailwind v4+ (not backwards-compatible with v3)
- Projects on v3 need migration guidance

## CSS Custom Properties Over Static Values

**Decision**: Define all brand tokens as CSS custom properties
**Rationale**:
- Runtime theming support (dark mode, user preferences)
- Cascading — components can override tokens locally
- DevTools-inspectable for debugging
- Compatible with any CSS framework, not just Tailwind

## Layer Ordering

**Decision**: Use explicit `@layer theme, base, clerk, components, utilities`
**Rationale**:
- Prevents specificity conflicts between framework layers
- Clerk auth components get their own layer to avoid style clashes
- Utilities always win (last layer), matching Tailwind expectations
- Theme layer loads first, establishing design tokens before anything else

## Color Palette Structure

**Decision**: Three-tier shade system (50, 600, 700) per color family
**Rationale**:
- Minimal palette covers common use cases: background (50), base (600), hover/dark (700)
- Avoids over-engineering 10-shade palettes that mostly go unused
- Easy to extend later without breaking existing usage
- Follows established pattern from Tailwind's default palette

**Trade-offs**:
- Limited shade options compared to full 50-950 spectrum
- Complex gradient designs may need additional intermediate shades

## Geist Font Selection

**Decision**: Geist Sans and Geist Mono as default fonts
**Rationale**:
- Modern, clean typeface designed for digital interfaces
- Excellent monospace variant for code display
- Variable font support for optimal file size
- Ships as an npm package (easy installation)
- Used by Vercel/Next.js ecosystem (consistent with deployment target)

## Grid Background Pattern

**Decision**: CSS-only repeating-linear-gradient instead of SVG or image
**Rationale**:
- Zero additional HTTP requests
- Infinitely scalable with no pixelation
- Tiny CSS footprint (~200 bytes)
- Easy to customize (gap size, line color, opacity)

## Plugin as Design System Reference

**Decision**: Plugin acts as a design system reference and application guide, not just a CSS file dump
**Rationale**:
- Claude Code agents benefit from contextual guidance (when to use which color)
- WCAG compliance information prevents accessibility issues
- Usage examples speed up integration
- Design guidelines maintain brand consistency across developers
