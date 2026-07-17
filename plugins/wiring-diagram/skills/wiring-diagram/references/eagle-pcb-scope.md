# Eagle / KiCad boundary — what this skill does NOT do

This skill makes **pictorial wiring diagrams** (breadboard photos + colored wires). That is a
different job from schematic capture and PCB layout. Keep them separate; do not bolt Eagle onto
the wiring pipeline.

## Three different artifacts

| Artifact | What it is | Tool | For whom |
|---|---|---|---|
| **Pictorial wiring diagram** | Photo-like parts + wires you can physically follow | **this skill** (Fritzing graphics) | someone who wires by looking, cannot read schematics |
| **Schematic** | Symbolic circuit (nets, symbols, no physical layout) | Eagle / KiCad schematic editor | someone who reads schematics |
| **PCB layout** | Copper, footprints, board outline for fabrication | Eagle / KiCad PCB editor | fabricating a board |

The reader here cannot read schematics — that is the entire reason the diagrams are pictorial.
Never answer a "how do I wire this" request with a schematic.

## Where Eagle actually fits

Eagle matters for **PCB projects** (e.g. a custom board), not for hookup diagrams:
- **Schematic symbols** and **PCB footprints** live in Eagle `.lbr` libraries.
- Use Eagle (or KiCad — free, and the more common modern choice) when the deliverable is a
  fabricated board: place footprints, route copper, export Gerbers.

## The `eagle2fritzing` bridge (only if a part is Eagle-only)

`github.com/fritzing/eagle2fritzing` converts EAGLE parts into Fritzing part format. It is
relevant in exactly one narrow case: a component exists in Eagle's libraries but has **no
Fritzing breadboard graphic**, and we need its pictorial for a wiring diagram. Then convert it
to a Fritzing part and add it via the normal add-a-part flow (`README.md`, `fritzing.py`).

For everything else, the Fritzing parts library already has the breadboard graphic, and
`eagle2fritzing` is unnecessary. It is a C++ build — treat it as a last resort, not a
dependency.

## Rule of thumb

- "Show me how to wire X" → this skill (pictorial).
- "Draw the schematic / design a PCB / make a board" → Eagle or KiCad, a separate track.
- "Fritzing has no picture for this part" → author one from its `.fzp`, or (Eagle-only part)
  convert via `eagle2fritzing`, then add it here.
