# wiring-diagram

Turn a short JSON spec into a **pictorial wiring diagram** — real Fritzing breadboard part
graphics with clean, colored point-to-point wires — rendered offline and headless. The kind of
diagram a beginner can actually follow to wire a circuit, not an abstract schematic.

Built because making these by hand (or asking an AI to "draw a wiring diagram") reliably fails:
you get hand-traced SVG blobs, ASCII art, or schematics a non-EE can't read. This skill packages
a working generator plus the hard-won rules so the result is repeatable.

## Install

```
/plugin add Human-Frontier-Labs-Inc/human-frontier-labs-marketplace/wiring-diagram
```

## What it does

Describe a circuit as **parts + a net list + rough positions**. The generator handles everything
that makes a diagram readable — part sizing, pin labels, leg ordering, obstacle-aware wire
routing around chips, z-order, and shared-rail (5V/GND) fan-out — automatically.

```sh
uv run python3 gen.py <spec.json> [out.png]
uv run python3 gen.py selftest        # label-rule self-check
```

The skill (`skills/wiring-diagram/SKILL.md`) tells Claude when and how to drive it. Rendering is
fully self-contained (vendored part SVGs); the full Fritzing parts repo is needed only to add a
new part. Worked specs + rendered PNGs are in `skills/wiring-diagram/examples/`.

## Scope

- **Does:** pictorial breadboard-style hookup diagrams for ESP32 / Pi / Arduino / discrete parts.
- **Does not:** schematic capture or PCB layout — that is Eagle / KiCad (see
  `skills/wiring-diagram/references/eagle-pcb-scope.md`).

## Honest note on validation

This is a **tool-wrapper / capability skill**, not a taste skill: its value is the bundled
deterministic generator and a redirect away from a documented failure (hand-drawn SVG /
unreadable schematics), not "teaching the model better wiring taste." A 4-cell taste benchmark
does not apply here; correctness of the generator is verified by its self-test and example
renders. Use it, and file issues where the output or a missing part gets in your way.

## Attribution & licensing

- **Code** (`gen.py`, `fritzing.py`, the render harness): MIT.
- **Breadboard part graphics** under `skills/wiring-diagram/parts/svg/`: from the
  **[Fritzing parts library](https://github.com/fritzing/fritzing-parts), CC-BY-SA 3.0** —
  redistributed here under that license with attribution. See
  `skills/wiring-diagram/parts/CREDIT.txt` for per-part credits (incl. the ESP32-C3 SuperMini
  part by 'vanepp'). Any derivative of those SVGs remains CC-BY-SA 3.0.
