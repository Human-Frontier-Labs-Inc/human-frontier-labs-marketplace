# Cross-platform Expo pitfalls (the long catalog)

Distilled from a shipped Expo app (App Store 2026; SDK 54, RN 0.81.5, expo-router 6, RevenueCat IAP) plus Expo's own docs. SKILL.md carries the load-bearing rules; this is the detail you reach for when a specific area bites.

## Platform divergence — full list
- **`KeyboardAvoidingView` `behavior`** — `"padding"` (iOS), `undefined` (Android). `"height"` on Android breaks scroll.
- **`Alert.prompt`** — iOS-only; silent no-op on Android. `if (Platform.OS === "ios" && Alert.prompt) {...} else { /* modal */ }`.
- **`expo-haptics` in a critical path** — awaiting `notificationAsync()` on Android can hang and strand the user (seen blocking sign-out). Fire-and-forget.
- **Android edge-to-edge** (`edgeToEdgeEnabled: true`) — transparent status bar; wrap top content in `SafeAreaView` or it slides under the notch. iOS/web unaffected.
- **Android 14 predictive back** — broke expo-router nav animations; opt out with `predictiveBackGestureEnabled: false` until your nav handles it.
- **`Pressable` vs `TouchableOpacity` on web** — different hit-target semantics; some components branch `Platform.OS === 'web' ? View : Pressable`.
- **NativeWind classes** — most Tailwind utilities map, but some grid/flex tricks don't translate to native. Test layout on a device, not just web.
- **Fetch `Headers` object** — `getRequestHeaders()`-style helpers return a Fetch `Headers`, not a plain object; iterating it as `{}` silently misses values (bites on web too).

## Native modules & New Architecture
- One native module → development build (dev-client). Expo Go can't load custom/RC-stage native code.
- SDK 55+ is New-Architecture-only (Fabric/TurboModules, bridgeless), can't be disabled. Some older native modules still break under it — verify each new dep on a **real device**.
- React Compiler (when enabled experimentally) can over-memoize → stale closures. If a re-render "isn't happening," suspect it first.

## EAS Build / Update
- `eas.json`: `appVersionSource: "remote"` + production `autoIncrement: true` → bump build numbers via EAS, never by hand-editing `app.json` for prod.
- **Pin the EAS Node version** in build profiles (e.g. `"node": "25.9.x"`) to match your local toolchain — a mismatch makes builds compile locally but fail on EAS with cryptic lockfile-resolution errors.
- Keep `package-lock.json` in sync (`npm install`, commit the lock) — transitive-dep drift randomly breaks EAS builds.
- **EAS Update is the unlock**: wire it before you ship, so UI fixes go out in ~60s instead of a 1–2 day store review. But respect `runtimeVersion` — JS bundles only reach binaries on a matching runtime; native changes still need a new build + store release.
- `runtimeVersion: { policy: "appVersion" }` ties each native release to its own OTA lane automatically; verify EAS picks up the bump on native changes.

## Env / secrets
- `EXPO_PUBLIC_*` → embedded in the JS bundle = PUBLIC. Use for: Clerk publishable key, API/BFF base URL, RevenueCat publishable per-store keys (`appl_*`, `goog_*`).
- No prefix → build-time only, absent at runtime. Secrets (`sk_*`, Stripe/Clerk secret) live server-side only, never in the mobile binary.
- Share the *same* publishable keys across web (`NEXT_PUBLIC_*`) and native (`EXPO_PUBLIC_*`) for cross-rail auth; document it in `.env.example` so nobody forks it.
- For builds, EAS environment variables (`eas env:list <env>`) are the source of truth — `.env.local` is for local device builds only.
- On-device secrets (session tokens) → `expo-secure-store` on native; web falls back to its localStorage shim.

## Maintainability patterns (each gated by the scale that earns it — don't add early)
- **Wrap an SDK in your own module** (e.g. `lib/rc-context.tsx`) — *when* it's called from many screens or is upgrade-prone (auth, payments). A one-call, stable SDK doesn't need a wrapper; calling it directly is the lazy-correct move. The wrapper earns its keep at the first painful upgrade, not before.
- **Order matters on identity-bearing SDKs** (always — this is correctness): configure before login, then attach the user id (e.g. RevenueCat `configure({appUserId: undefined})` then `logIn(userId)` once auth is ready). Reversed = purchases/events silently attach to an anonymous id that never matches your real user.
- **Own your paywall/critical UX in JS** instead of a vendor remote-UI component — *when* past MVP: JS-only iteration, full design control, stores increasingly require UX changes via JS not native re-review. Use the vendor's component to ship the MVP.
- **A crash gate** (on-screen banner catching launch crashes that vanish before logs) — *when* you actually hit silent launch crashes (common on Android). ~130 LOC; don't pre-build it.
- **A separate mobile BFF** from the web app's API routes — *when* mobile and web auth/rate-limits/needs have actually diverged. Until then, reusing the existing backend is fine; a second service is premature.

## App Store reality
- Rejections, not code, are the long pole for subscription apps. Guideline 3.1.1 (in-app purchase) commonly bites several cycles before metadata/flow match Apple's model. Budget 2–3 rejection rounds.

## Version pins that mattered (one shipped config, mid-2026 — verify against current SDK)
```
expo                       ~54.0.x      react 19 + RN 0.81.x
react-native               0.81.x
expo-router                ~6.0.x       typed routes on
react-native-purchases     ^10.4.0      autolinks — do NOT register as a plugin
expo-secure-store          latest       Clerk session tokens
node (eas.json)            pinned       match local toolchain
```
Don't bump a payments/IAP SDK minor without re-running the purchase→entitlement→provision test. Re-test SDK upgrades on a real Android device.
