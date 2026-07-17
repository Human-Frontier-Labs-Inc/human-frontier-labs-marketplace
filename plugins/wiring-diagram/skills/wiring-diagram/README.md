# diagram — parametric pictorial wiring diagrams

Spec JSON → a Fritzing-style wiring picture (real photographic board graphics + clean
colored point-to-point wires). Offline, headless (Chromium screenshot). Board graphics:
Fritzing parts library (CC-BY-SA 3.0).

```sh
uv run python3 gen.py <spec.json> [out.png]
```

## The idea: you describe the circuit, the generator draws it

A spec is **parts + nets + rough positions**. Everything that makes a diagram *readable*
is a rule the generator applies for you — you never hand-tune it per build. The nuances we
used to fix by hand are now automatic:

| Nuance | Rule (automatic) |
|---|---|
| Part size | Per-part default width (`DEFAULT_W`). Override with `"w"` only if you want. |
| Leg labels on ICs / transistors / pots | Auto-stamped from the part's real connector names, shortened (`Vcc Supply Voltage`→`VCC`, `Threshold`→`THR`, `E`/`B`/`C`…). Only *connected* legs get a label. Override per-part with `"pinlabels"` for a semantic name (e.g. a pot leg labeled by what it feeds). |
| Which leg of a resistor faces which neighbor | Auto-assigned to whichever ordering doesn't double a wire back over the body. Resistors are electrically reversible, so the spec never has to care which leg is "Pin 0". |
| Wires hidden behind parts | Wires render above the board graphics (z-order), connection dots on top. |
| Wires cutting across a chip to reach a pin | Obstacle-aware router: each wire tries many candidate paths, scores `crossings×100000 + length`, routes *around* parts and approaches each pin from open space. |
| Shared nets (5V, GND) becoming a rat's nest | Declare a `bus` rail; each wire drops perpendicular to it at its own x. |

What's left for you to author: **rough part positions** (`x`,`y`) and the **net list**
(`wires`). Position is the one real design choice — where things sit on the page — and it's
now the *only* manual step. Labels, sizing, leg-ordering, routing, and layering are the
generator's job.

### Placement tips (the authored part)
- Put parts that connect to a chip's **top** pins *above* the chip, **bottom** pins *below* —
  wires then drop straight in instead of climbing around the side.
- Give a dense sub-circuit (e.g. a 555 timing network) its own quadrant with space; the
  router is good but it can't uncrowd a cramped placement.
- Stand a single power resistor **vertical** (`"rotate": 90`) above its pin so its supply
  wire drops straight down and doesn't share a lane with signal wires.

## Spec format

```json
{
  "title": "shown top-left",
  "width": 1900, "height": 1020,
  "routing": "ortho",                         // "ortho" = right-angle + obstacle-aware (default);
                                              //   "curve" = organic bezier, NO obstacle avoidance
                                              //   (fine for 2-3 flat parts; use ortho if any part is tall)
  "components": [
    { "type": "bus", "id": "v5", "x1": 210, "x2": 1850, "y": 150, "label": "5V", "color": "red" },
    { "id": "u1",  "part": "ne555", "x": 560, "y": 420 },                 // size + labels automatic
    { "id": "r1",  "part": "resistor", "x": 600, "y": 230, "rotate": 90, "label": "R1 10k" },
    { "id": "pot", "part": "pot", "x": 300, "y": 175, "label": "100k SPEED",
      "pinlabels": { "wiper": "WIP", "leg1": "THR" } }                    // optional semantic override
  ],
  "wires": [
    { "from": ["power","5.0V"], "to": ["v5"], "color": "red" },           // 1-element endpoint = tap a bus
    { "from": ["u1","Output"],  "to": ["r3","Pin 0"], "color": "blue" }
  ]
}
```

- **component**: `id` (unique), `part` (a key in `parts/index.json`), `x`,`y`. Optional
  `w`, `rotate` (deg), `label`, `labelpos` (top/bottom/left/right), `pinlabels`.
- **bus**: `type:"bus"`, `id`, `x1`,`x2`,`y`, `label`, `color`. A horizontal shared rail.
- **wire**: `from`/`to` are `[componentId, pinName]`, or `[busId]` (1-element) to tap a rail.
  Pin names are the part's real Fritzing connector names — see `parts/index.json`
  (e.g. ne555 has `Vcc Supply Voltage`, `Discharge`, `Threshold`, `Trigger`, `Output`,
  `Reset`, `Ground`, `Control Voltage`; resistor has `Pin 0`/`Pin 1`; led has `anode`/`cathode`).
- **color**: name (red/black/green/blue/orange/violet/brown…) or hex.

## Parts

`parts/index.json` maps a short slug → the vendored Fritzing breadboard SVG + its
connector→terminal ids. Current: `ne555`, `resistor`, `pot`, `led`, `ecap`, `cerc` (ceramic
cap), `npn`, `power`, `lm386` (audio amp), `speaker`, `piezo`. The `lm386` body is a
hand-authored generic DIP-8 — copy its SVG and relabel the face + pin map for any other DIP-8.
Add one by dropping the `.fzp`+SVG under `parts/` and running `fritzing.py` to resolve the
pin map (see `fritzing.py`; the full Fritzing repo is the source, CC-BY-SA — credit it).

## Self-check

```sh
uv run python3 gen.py selftest      # asserts the label-shortener rules
```

Rendering the live spec (`firmware/flicker-lamp/wiring-fzp.json`) is the integration test —
it exercises auto-labels, auto leg-assignment, bus taps, obstacle routing, and rotation.
