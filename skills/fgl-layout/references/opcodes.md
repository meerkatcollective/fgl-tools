# FGL Opcode Catalog

This is the canonical opcode list the validator's `KNOWN_OPCODES` dict accepts. Anything outside this list will trigger `FGL001`. Arities (the integer arguments inside `< >`) are validated by `FGL002`.

Source of truth: `src/fgl_validator/rule_set.py:KNOWN_OPCODES` in this repo. Keep in sync.

Notation: `<OP>` = 0 args, `<OP n>` = 1 arg, `<OP n,m>` = 2 args. Opcodes are case-sensitive — `RC` ≠ `rc`.

## Rotation (0 args each)

| Opcode | Meaning |
|--------|---------|
| `<NR>` | Normal (no rotation) |
| `<RR>` | Rotate right 90° |
| `<RU>` | Rotate up 180° |
| `<RL>` | Rotate left 270° |

## Layout / cursor

| Opcode | Args | Meaning |
|--------|------|---------|
| `<RC r,c>` | 2 | Set cursor row/column |
| `<SP r,c>` | 2 | Set position (logo recall anchor) |

## Fonts

| Opcode | Args | Meaning |
|--------|------|---------|
| `<F n>` | 1 | Select resident font by id |
| `<TT n>` | 1 | TrueType select (single arg) |
| `<TTF n,m>` | 2 | TrueType select with size |
| `<RTF n,m>` | 2 | Rotated TrueType select |
| `<HW h,w>` | 2 | Height × width multiplier (default `<HW6,6>`) |
| `<SD n>` | 1 | Set dot size / font width step |

## Lines and boxes

| Opcode | Args | Meaning |
|--------|------|---------|
| `<LT n>` | 1 | Line thickness (resets to 1 after each box/line) |
| `<BS r,c>` | 2 | Box start corner |
| `<BX r,c>` | 2 | Box end corner |
| `<VX n>` | 1 | Vertical line of length n |
| `<HX n>` | 1 | Horizontal line of length n |

## Logos and graphics

| Opcode | Args | Meaning |
|--------|------|---------|
| `<LD n>` | 1 | Recall downloadable logo by id |
| `<LO n>` | 1 | Logo (legacy) |
| `<G n>` | 1 | Binary graphics strip |
| `<g n>` | 1 | ASCII-hex graphics strip (preferred) |

## Buffer / repeat

| Opcode | Args | Meaning |
|--------|------|---------|
| `<CB>` | 0 | Clear buffer |
| `<RE n>` | 1 | Repeat last element n times |

## Inverse and transparent

| Opcode | Args | Meaning |
|--------|------|---------|
| `<EI>` | 0 | Enable inverted print |
| `<DI>` | 0 | Disable inverted print |
| `<t>` | 0 | Transparent text mode |
| `<n>` | 0 | Normal (opaque) text mode |

## Barcode setup

| Opcode | Args | Meaning |
|--------|------|---------|
| `<X n>` | 1 | Bar width multiplier (use `<X3>` at 300 dpi) |
| `<BI>` | 0 | Bar inhibit |
| `<AXB n>` | 1 | Alternate barcode setup |
| `<FL n>` | 1 | Flag-length |

## Ladder (vertical) barcodes — 1 arg each

`<Ul n>`, `<EL n>`, `<NL n>`, `<CL n>`, `<OL n>` — UPC, EAN, Codabar/Code39, Code128, Interleaved 2 of 5 ladder variants. Use lowercase second char (`<oL4>`, `<nL4>`) for rotation-aware versions.

## Picket-fence (horizontal) barcodes — 1 arg each

`<UP n>`, `<EP n>`, `<NP n>`, `<FP n>`, `<CP n>`, `<OP n>` — same symbologies, picket-fence orientation.

## Output / control

| Opcode | Args | Meaning |
|--------|------|---------|
| `<PL n>` | 1 | Print length |
| `<RO n>` | 1 | Reverse order |
| `<ME>` | 0 | Mark eject |
| `<MD>` | 0 | Mark detect |
| `<TRE>` | 0 | Test run / eject |

## Status

| Opcode | Args | Meaning |
|--------|------|---------|
| `<S n>` | 1 | Status query |
| `<PC>` | 0 | Print count |
| `<TC n>` | 1 | Total count |

## Variables

| Opcode | Args | Meaning |
|--------|------|---------|
| `<VA n>` | 1 | Variable substitution (e.g. `<VA1>` … `<VA113>`). The validator does not constrain n. |

## Terminators (all lowercase, 0 args)

| Opcode | Meaning |
|--------|---------|
| `<p>` | Print + cut |
| `<q>` | Print, no cut |
| `<z>` | Eject (no print) |
| `<h>` | Hold |
| `<r>` | Hold image / register |

A segment that does not end with one of these triggers `FGL004`. Multi-ticket streams can chain segments — each must terminate.

## Lowercase opcodes that are NOT terminators

`<t>` (transparent text) and `<n>` (normal text) and `<g>` (ASCII-hex graphics) are lowercase but are not segment terminators.
