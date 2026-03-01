# Changelog

All notable changes to Chuqlab CSS Theme will be documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-02-28

### Added

**Brand Design System:**
- Chuqlab brand color palette (primary navy, secondary red, accent blue)
- Extended color shades (50, 600, 700 for each palette)
- Success color palette for positive states
- Light and dark background tokens

**Typography:**
- Geist Sans font configuration
- Geist Mono font configuration
- CSS custom property setup for font variables

**Tailwind CSS v4 Integration:**
- Native `@theme` directive with all brand tokens
- `@layer` ordering (theme, base, clerk, components, utilities)
- Tailwind v4 border color compatibility layer

**Utility Classes:**
- `.background` — Subtle grid pattern overlay for landing pages
- `.mask` — Fade-in/fade-out gradient mask for scrollable areas

**Documentation:**
- Complete SKILL.md with color reference, typography guide, and usage examples
- Design guidelines with WCAG contrast compliance
- Installation guide for Next.js, Vite, and plain HTML projects

### WCAG Compliance

All primary color combinations verified against WCAG AA:
- Primary navy on white: 14.5:1 (AAA)
- Secondary red on white: 4.6:1 (AA)
- Accent blue on white: 5.2:1 (AA)
- Success green on white: 5.1:1 (AA)

## [Unreleased]

### Planned

- Dark mode variant with inverted palette
- Component-specific token presets (buttons, cards, forms)
- Figma design token export
- CSS-in-JS adapter (styled-components, Emotion)
