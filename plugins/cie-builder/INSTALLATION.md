# CIE Builder Installation

## From Marketplace

If you have the Human Frontier Labs marketplace installed:

```bash
/plugin add Human-Frontier-Labs-Inc/human-frontier-labs-marketplace/cie-builder
```

## Install Marketplace First

```bash
/plugin marketplace add Human-Frontier-Labs-Inc/human-frontier-labs-marketplace
```

## Manual Installation

1. Clone or copy the `cie-builder/` directory into your `.claude/skills/` folder
2. Ensure `SKILL.md` is at the root of the skill directory
3. Place reference files under `references/`
4. Place scripts under `scripts/`

## Prerequisites

- Claude Code CLI installed
- GCP project with billing enabled (for actual deployment)
- Go 1.21+ (for backend development)
- Node.js 18+ (for frontend development)
- Docker (for local development)

## Verification

After installation, test by saying:
```
"resume CIE work"
```

The skill should activate and run build state detection.
