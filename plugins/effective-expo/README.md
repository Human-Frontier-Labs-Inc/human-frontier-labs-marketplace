# effective-expo

Architecture taste for building **cross-platform Expo apps** (iOS, Android, web) from one codebase — the steering that keeps a growing app factored **without over-building it**.

A frontier model writes correct Expo code from a single prompt. Over a multi-turn build it drifts two opposite ways: toward **mush** (god-screens, logic inlined everywhere, the UI DRY'd across web and native until it breaks) and toward **over-build** (a monorepo for one app, a wrapper around a one-call SDK, a server cron job for something the phone could do locally). This skill is the anchor you re-apply every turn so the app stays factored *and* stays small.

## The one idea
**Share the brains, not the UI** — and only the structure the app has actually earned. TypeScript logic is shared; the UI is rebuilt per-platform (web DOM libraries don't run on native); and every layer of structure waits until something real needs it.

## What's inside
- `skills/effective-expo/SKILL.md` — the anchor: the share-the-brains boundary, expo-router as the spine, a "start lazy / add structure when it earns its place" table, the platform-divergence rules, the version-specific SDK/config facts the model gets stale on (autolinking, New Architecture, `runtimeVersion` OTA semantics, `EXPO_PUBLIC_` secrets), and a per-turn check that catches **both** drift toward mush and drift toward over-build.
- `skills/effective-expo/references/cross-platform-pitfalls.md` — the full pitfall catalog, EAS/env detail, and version pins, each heavier pattern marked with the scale that justifies it.

## How it was built
Grounded in **canonical Expo documentation** (gathered comprehensively, not cherry-picked) plus a real shipped cross-platform app's hard-won failure list — never anyone's sloppy repo. Then validated and hill-climbed on the axis that matters: a non-expert accreting an app over many turns. See `benchmarks/RESULTS.md`.

Pairs well with a "lazy senior" discipline — the skill treats over-engineering as a first-class failure, not just god-files.
