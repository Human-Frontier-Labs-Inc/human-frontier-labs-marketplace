---
name: effective-expo
description: Architecture guidance for building and maintaining cross-platform Expo apps (iOS, Android, web) from one codebase — the taste that keeps a growing app factored without over-building it. Use when building or extending an Expo / React Native app, setting up an Expo + Next.js monorepo, writing expo-router navigation, sharing code across native and web, styling with NativeWind, wrapping native SDKs, or configuring EAS Build/Update. Triggers on "expo app", "react native app", "build a mobile app", "ios android web", "expo router", "expo monorepo", "eas build", "nativewind".
---

# Effective Expo

A frontier model writes correct Expo code from a single prompt, then **drifts over a multi-turn build** — two opposite ways:
- **toward mush:** god-screens, logic inlined everywhere, the UI DRY'd across web and native until it breaks;
- **toward over-build:** a monorepo for one app, a wrapper around a one-call SDK, a BFF and a crash gate before there's a single user.

A lazy senior avoids both. This skill is the anchor: re-apply it each turn so the app stays factored **and** stays small.

## The one idea

**Share the brains, not the UI** — *and only the structure the app has actually earned.* TypeScript logic is shared; the UI is per-platform; and every layer of structure waits until something real needs it.

## Start lazy, add structure when it earns its place

| You have… | Do this | Add the heavier thing **when** |
|---|---|---|
| A mobile app only | One Expo app: `app/` (routes) + `components/` + `lib/` (logic). No monorepo, no `packages/`. | …web and native need the **same TypeScript**. Then add the monorepo + `packages/`. |
| Logic you reuse in 2 screens | A function/hook in `lib/`. | …it's reused across **apps** → promote it to `packages/`. |
| An SDK called in one place | Call it directly. | …it's called from **many screens** or is **upgrade-prone** (auth, payments) → wrap it once in `lib/`. |
| An MVP | Ship the screens. | …a real pain shows up (silent crashes, store-review friction) → *then* add a crash gate / custom paywall / BFF. |
| A "remind me / notify me" feature | An on-device local notification the phone schedules with itself (`expo-notifications`); web is a no-op. **No server.** | …it must fire **while the app is closed for days** AND can't be re-derived on app-open (depends on other users, or a server clock the phone can't poll) → *then* a scheduled job. A backend merely *storing* the data isn't enough — the phone fetches it on open and schedules locally. |

Never add a layer "for the other platforms later." Later can add it in one commit; today it's dead weight.

## The boundary (once you have web + native)

- **Never share UI across web ↔ native.** Web-only DOM libraries (radix, shadcn, anything touching `document`) do not run on native or react-native-web. The native UI is a *rebuild* in RN primitives + NativeWind, not a port. **Duplicating a 30-line component beats fighting the boundary with a shared package.**
- **`packages/` holds only shared TypeScript** — types, API client, domain logic, validation. Never UI. (`create-t3-turbo` is the structural reference *if* you've reached monorepo scale.) Metro auto-configures monorepos since SDK 52 — don't hand-write `watchFolders`/`resolver` unless you're pre-52.
- **Business logic lives in `lib/`/`packages/`, not in screens.** A screen wires params to components and hooks; it holds no business logic. But *derived render state* — a filter/sort/format computed from already-loaded data for one screen — stays in the screen; promoting it to `lib/` with a single caller is the over-build. Re-applied each turn, this stops the god-screen without inventing an abstraction the screen didn't need.

## expo-router is the spine

- File-based routes in `app/`; `_layout.tsx` defines nav; group folders `(group)` organize without adding a URL segment; turn on typed routes. **Use the file system — don't build a navigation abstraction over it.**
- Screens stay thin: reusable UI → `components/`, logic → `lib/`. That's the whole pattern; resist more.

## Platform divergence (prefer the one-liner)

Expo's own rule: **inline `Platform.OS` / `Platform.select` for one-liners; promote to a platform-extension file (`.ios.tsx` / `.android.tsx` / `.web.tsx` / `.native.tsx`) only when a *whole* component diverges.** Don't reach for a platform file when a one-line check does it.
- In `app/` (routes), a platform file needs a **non-platform sibling** (routes stay universal for deep linking). For genuinely different screens, build the variants in `components/` with extensions and re-export one as the route.

Things AI writes wrong on native (fix on sight — these are bugs, not style):
- `KeyboardAvoidingView` `behavior`: `"padding"` (iOS), **`undefined`** (Android — `"height"` breaks scroll).
- `Alert.prompt` is **iOS-only**; silent no-op on Android. Guard + modal fallback.
- Don't `await` `expo-haptics` in a critical path (e.g. sign-out) — can hang on Android. Fire-and-forget.
- Android edge-to-edge: content slides under the notch without `SafeAreaView`.
- `Pressable` vs `TouchableOpacity`: different hit-targets on web.

## SDK & config facts the model gets stale on (correctness — don't simplify these away)

- **Autolinking:** modern native libs autolink — do **not** add them to `plugins`. (`react-native-purchases` v10 autolinks; v9 needed a plugin, so the model suggests the v9 way.) Add a config plugin only if the lib's *current* docs say so.
- One native module → you're on a **dev build** (dev-client); Expo Go is done.
- **New Architecture:** SDK 55+ is New-Arch-only, can't be disabled (SDK 54 for legacy). Test every new native dep on a **real device**.
- **`runtimeVersion`:** every native release is its own OTA lane; EAS Update JS only reaches matching `runtimeVersion` — don't promise an OTA fix to users on an older binary.
- **Env:** `EXPO_PUBLIC_*` is embedded in the client bundle = **public** (publishable keys, base URLs). Secrets (`sk_*`, Stripe/Clerk secret) never get the prefix; server-side only. For builds, EAS env vars are the source of truth, not local `.env`.

## The check (run every turn you touch the app)

Drifting toward mush?
1. New *business* logic inlined in a screen instead of `lib/`/`packages/`? → move it. (Derived render state — a filter/sort/format over already-loaded data for one screen — stays put; lifting it to `lib/` for one caller is the over-build.)
2. Sharing across web↔native that isn't pure TypeScript? → it can't; rebuild the UI.
3. A screen growing business logic? → extract.

Drifting toward over-build?
4. A monorepo/`packages/` with one app, or a wrapper with one caller and a stable SDK? → delete it; use `lib/` / call directly.
5. A BFF / crash gate / custom paywall / platform abstraction added before a real need? → YAGNI; add when it bites.

The right answer is usually the smaller one. Pairs well with the `ponytail` skill.

## Pointers
- `references/cross-platform-pitfalls.md` — full pitfall catalog, EAS/env detail, version pins. Each "heavier" pattern there is marked with the scale that justifies it.
