# effective-expo — validation summary

Validated on the axis that matters for a language/framework skill: **multi-turn drift** — a non-expert who can't read code accreting a cross-platform Expo app over several turns, skill arm vs a no-skill baseline, **same frontier model both arms**, blind-judged on the final codebase. Two task batteries, hill-climbed across 5 iterations. Honest numbers below, including what went wrong.

## The task
A non-expert builds a client-notes app over time:
- **Base battery (4 turns):** mobile-only → add auth → add web (the share-brains-not-UI boundary) → cross-platform search.
- **Hard battery (5 turns):** … → cross-platform paid plan (App Store IAP on native + Stripe on web) → push/reminder notifications. This baits the gnarly real-world gotchas: SDK autolinking, secrets-not-in-`EXPO_PUBLIC_`, platform-split payments, local-vs-server scheduling.

## Metric
A **drift score** = sum of countable BAD signals on the final codebase, penalizing **both** mush (god-files, logic-in-screens, UI shared across the web/native boundary, SDK called from a screen) **and** over-build (premature abstraction, unrequested infrastructure). Plus a blind pairwise judge ("which would a senior rather own and extend") and a count of known platform bugs.

## Headline (the number to trust)
Across **10 head-to-head builds, the skill beat no-skill 9-1 pairwise** (base battery 4-0, hard battery 5-1). Encoded correctness held throughout: **known platform bugs — skill 0, baseline up to 1** (the skill arm never registered an autolinked lib as a config plugin, never put a secret key in an `EXPO_PUBLIC_` var, and got the platform-split payment right).

## What the hill-climb actually bought
The loop's real product was finding and closing **two over-engineering holes the skill itself was originally causing**:
1. An unqualified "logic goes in `lib/`" rule made a chain promote a 3-line render filter into a `lib/` function with one caller. Fix: scope to *business* logic; derived render state stays in the screen.
2. A loose escalation clause let a chain build a server cron + Edge Function + DB columns for a "remind me on my phone in 30 days" feature. Fix: a default-to-on-device-local-notification rule; escalate to a server job only when the notification must fire while the app is closed for days and can't be re-derived on open.

Net change to the skill from hill-climbing: **more restraint, not more rules.**

## Honest caveats
- The raw drift integer in the hard battery is **not** a clean monotonic improvement line. One iteration regressed from a too-loose patch (caught and fixed the next round), and the final iteration's score was inflated by a grader artifact (the rubric counted the user-*requested* payment path as "premature infra"). The trustworthy signal is the pairwise result plus the code-inspected diagnoses, not the absolute integer.
- Evidence strength is 2 build chains per arm — below an ideal N≥5. Strong enough to ship; a higher-N confirmation run would harden the final number.

Method: built with the `building-effective-skills` discipline (gather canonical authority → detect baseline → distill only the gap under lazy-senior restraint → validate on the multi-turn drift axis).
