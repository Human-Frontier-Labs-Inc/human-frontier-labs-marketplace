---
name: wiring-diagram
description: >-
  This skill should be used whenever the user asks to "make a wiring diagram", "update the
  wiring diagram", "fix the diagram", "show me how to wire this", "draw a hookup guide", or
  otherwise wants a picture of how components connect for an ESP32/Pi/Arduino/discrete-component
  build. It generates a PICTORIAL breadboard-style diagram — real Fritzing part photos + clean
  colored point-to-point wires, rendered offline and headless from a small JSON spec — NOT a
  schematic, because the reader cannot read schematics. It must not be used for PCB layout or
  schematic capture (that is Eagle/KiCad).
license: MIT
metadata:
  provenance: packaged from builder-area/tools/diagram (Willy's generator)
  parts_graphics: Fritzing parts library (CC-BY-SA 3.0)
---

# Wiring Diagram Generator

Turn a circuit description into a **pictorial wiring picture**: real Fritzing breadboard part
graphics + clean colored wires drawn pin-to-pin. Offline, headless (Chromium screenshot). The
reader looks at it and sees *where each wire physically goes* — no schematic literacy required.

## The one principle

**Author parts + a net list + rough positions. The generator does everything that makes it
readable.** Part sizing, leg labels, which leg faces which neighbor, wire routing around chips,
z-order, and shared-rail fan-out are all automatic rules — never hand-tuned per diagram.

```sh
uv run python3 gen.py <spec.json> [out.png]
uv run python3 gen.py selftest        # asserts the label-shortener rules
```

## Hard rules (this is why the skill exists — do not regress)

1. **NEVER hand-draw or hand-trace SVG/paths for a wiring diagram.** The whole point is real
   part graphics + a rule-based router. Hand-drawn parts were the old failure mode and are banned.
2. **NEVER screenshot the Fritzing desktop app.** Consume the parts library programmatically:
   vendored breadboard SVG + pin coordinates from the `.fzp` connector `terminalId`s.
3. **Pictorial, not schematic.** No schematic symbols, no ratsnest. If a request needs a
   schematic or PCB, say so and route it to Eagle/KiCad — see `references/eagle-pcb-scope.md`.
4. **Parametric authoring only.** A spec names parts, nets, and rough `x`/`y`. Do not set
   sizes, pin labels, or wire paths by hand — if the output is wrong, fix the *rule* or the
   *placement*, not the pixels. (`references/placement-routing.md`)
5. **Render is self-contained**; the Fritzing repo clone is needed ONLY to add a new part.
6. **Credit CC-BY-SA** for any Fritzing graphic used (see `parts/CREDIT.txt`).

## Workflow

1. List the parts and the net list (what connects to what). Map each part to a slug in
   `parts/index.json`; if one is missing, add it first (see `README.md`, Parts section:
   drop the `.fzp`+SVG under `parts/` and run `fritzing.py` to resolve the pin map).
2. Write a spec JSON: `components` (id, part, rough x/y), `wires` (`[id,pin]`→`[id,pin]`),
   optional `bus` rails for shared 5V/GND. Full format + a worked example: `README.md`.
3. Render: `uv run python3 gen.py spec.json out.png`.
4. Look at the PNG. If wires cross or crowd, **move parts** (placement is the real design
   choice) — put a chip's top-pin neighbors above it, bottom-pin below. Re-render. Iterate.
   (Placement + routing tips: `README.md`.)
5. Save the spec next to the firmware (`firmware/<project>/wiring-*.json`) so it regenerates.

## What each piece is

- `gen.py` — the generator (spec → PNG). Parametric rules live here (`DEFAULT_W`, `PIN_ALIAS`,
  the obstacle-aware router, bus fan-out).
- `fritzing.py` — part loader: resolve a Fritzing `.fzp` → breadboard SVG + pin map. Used only
  when **adding a part** (needs the `fritzing-parts` repo clone; set `FZ_REPO`).
- `parts/` — `index.json` (slug → SVG + connector→terminal map), the `.fzp`s, `svg/` (vendored
  breadboard graphics), `CREDIT.txt`.
- `examples/` — worked specs + their rendered PNGs (555 blink, LED array, NPN driver, pot
  dimmer, LM386 amp). Copy the closest one as a starting point.
- `references/eagle-pcb-scope.md` — the Eagle/KiCad boundary (schematic + PCB) and the
  `eagle2fritzing` bridge. Spec format, adding a part, and placement tips live in `README.md`.

## When NOT to use

- **Schematic capture** (symbolic circuit) or **PCB layout/footprints** → Eagle or KiCad, not
  this. `references/eagle-pcb-scope.md` explains the boundary and the `eagle2fritzing` bridge.
- A part with no Fritzing breadboard graphic and no time to author one → say so; do not
  substitute a hand-drawn box and call it done.
