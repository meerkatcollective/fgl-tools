---
name: fgl-layout
description: "Author BOCA Friendly Ghost Language (FGL) ticket layouts and convert images to FGL graphics. Use when the user wants to design a ticket for a BOCA Lemur / Ghostwriter printer (FGL22/24/26/42/44/46), edit an existing .fgl file, or turn a PNG/BMP logo into FGL <g#> hex. Triggers on 'FGL', 'Friendly Ghost Language', 'BOCA ticket', 'BOCA layout', 'Lemur', 'Ghostwriter', 'ticket layout', 'png to FGL', 'convert logo for ticket printer'."
model: opus
user-invocable: true
allowed-tools: Read, Grep, Glob, Write, Edit, AskUserQuestion, TodoWrite, Bash(python3 *), Bash(ls *), Bash(file *), Bash(cat *), Bash(wc *)
argument-hint: [description-or-fgl-or-image-path]
---

# FGL Layout

Ultrathink before emitting any FGL. A ticket is a 2D dot matrix at fixed dpi, every command sequence has side-effects on cursor state, and most beginner mistakes are coordinate-math errors — not syntax. Spend the first minutes confirming **printer model, dpi, ticket size, and the regions of the layout** before producing a single `<RC...>`.

This skill produces a `.fgl` text artifact ready to send to a BOCA printer, and optionally a paired image conversion when the layout includes a logo. It is not a printer driver — it does not transmit to the device.

**Input**: `$ARGUMENTS` — one of:
- A free-form ticket description (most common).
- A path to an existing `.fgl` file to edit.
- A path to an image (`.png`, `.bmp`, `.tif`) to convert into FGL graphics.

## Current Context

- **Branch**: !`git branch --show-current`
- **Last Commit**: !`git log -1 --oneline`
- **Existing FGL artifacts**: !`ls -t thoughts/shared/fgl/*.fgl 2>/dev/null | head -5 || echo "(none)"`
- **Skill bundle**: `references/`, `templates/`, `scripts/png_to_fgl.py`

## Initial Response

1. **`$ARGUMENTS` ends in `.fgl`** and the file exists → read it; begin **Step 4 (Edit)**.
2. **`$ARGUMENTS` matches `*.png|*.bmp|*.tif|*.tiff`** and the file exists → begin **Step 5 (Image-only)**.
3. **`$ARGUMENTS` is free-form prose** → begin **Step 1 (Confirm printer)**.
4. **`$ARGUMENTS` is empty**:
   ```
   I'll help you build an FGL ticket layout for a BOCA printer.

   Provide one of:
     1. A description:        /fgl-layout "2x5.5 event ticket with logo top-left, seat row right, code128 barcode bottom"
     2. An existing layout:   /fgl-layout thoughts/shared/fgl/concert.fgl
     3. An image to convert:  /fgl-layout assets/logo.png

   Default printer: BOCA FGL46 R2/8 SB07 @ 300 dpi, 2"×5.5" ticket (≈600 rows × 1650 cols).
   ```
   Then wait.

## The Context Principle

Every `AskUserQuestion` must brief the user in prose immediately before asking — name the regions, dimensions, or commands in full so option labels stay short. Never ask a question whose answer requires the user to remember an FGL command from memory; show the command in the brief.

---

## Step 1: Confirm printer + canvas + orientation

Before drafting, lock in these five numbers/states:

1. **Printer family**: FGL46 (Lemur, full spec), FGL44, FGL42, FGL26 (subset, no QR via FGL), FGL24/22.
2. **DPI**: 200 (dot size ≈.00492") or 300 (dot size ≈.00328").
3. **Ticket size**: width × length in inches. Default 2"×5.5".
4. **Margin**: BOCA reserves a small border; safe printable area is ~14 dots in from each edge.
5. **Orientation**: is the printer in default (`<rtd>`) or reverse (`<rte>`) orientation? Adjustable Lemur models in portrait mode **require** `<rte>` for proper formatting. If the layout's perforation should land on the user-view "left" side of the ticket, the printer needs `<rte>` set once at provisioning, and you need to author with the mirror helper from `references/orientation.md`.

Compute **dot rows × dot columns** for the canvas. Reference table for common sizes lives in `references/coordinate-math.md`.

Default if the user has not specified otherwise: **FGL46 @ 300 dpi, 2"×5.5" → 600 rows × ~1650 cols, default orientation**.

If orientation might already be set on the user's printer, ask. Don't try to detect it from the layout — `<rte>` is permanent flash state, not something the ticket stream re-asserts.

Use AskUserQuestion to confirm only when the user has not already supplied a printer/dpi (re-read the prior turn). If everything is already specified, skip this question and announce the assumed canvas in prose.

```
Question: "Confirm the canvas?"
Options:
  - "FGL46 @ 300 dpi, 2"×5.5" (600×1650 dots)" — the user's saved default; recommended.
  - "FGL46 @ 200 dpi, 2"×5.5" (400×1100 dots)" — guide's reference example; broader compatibility.
  - "Custom" — user will specify printer / dpi / dimensions.
```

---

## Step 2: Decompose the ticket into regions

Take the user's description and produce a region table **before** writing any FGL. Each region is one row:

| # | Purpose | Anchor (RC) | Size (rows×cols) | Rotation | Font / element |
|---|---------|-------------|------------------|----------|----------------|
| 1 | Logo | RC20,30 | 80×200 | NR | downloaded logo `<LD1>` |
| 2 | Event title | RC60,300 | 60×900 | NR | `<F2><HW3,3>` |
| … | … | … | … | … | … |

Show the table to the user in prose, then use AskUserQuestion to confirm:

```
Question: "Region layout look right before I emit FGL?"
Options:
  - "Looks good — emit the .fgl"
  - "Adjust regions" — user will say which row to change
  - "Start over" — re-decompose from scratch
```

This step is the most important — coordinate errors compound. If unsure, sketch in prose first.

---

## Step 3: Emit the FGL artifact

Write to `thoughts/shared/fgl/<slug>.fgl`. Slug from the user description (kebab-case, ≤40 chars). If the directory does not exist, create it via `mkdir -p` in a single Bash call.

Structure every layout this way:

```
<command-stream>          # one logical region per line, comments stripped
<p>                       # terminator (use <p>, not <FF> — many hosts strip 0x0C)
```

Use the templates in `templates/` as a starting scaffold:

- `templates/basic-ticket.fgl` — single-region "hello world" ticket.
- `templates/event-ticket.fgl` — multi-region with title, seat block, barcode, fine-print.

Copy the template, then edit the regions to match the table from Step 2. **Do not write FGL freehand** — start from a known-good template.

Critical rules to apply while editing:

1. **Reset cursor with `<RCr,c>` before every region.** The cursor only auto-advances within a region; cross-region jumps are explicit.
2. **Re-issue `<HWw,h>` and `<F#>` per region.** Width/height/font persist until changed but a long ticket gets safer with explicit re-statement.
3. **`<LT#>` resets to 1 after every box/line.** If you draw three lines of thickness 4, you must send `<LT4>` three times.
4. **Bar code data delimiters are mandatory and symbology-specific:**
   - Code 128 (`<oL#>` / `<OL#>`): `^DATA^` — e.g. `<X3><oL4>^ABC123^`
   - Interleaved 2 of 5 (`<fL#>` / `<FL#>`): `:DATA:` — e.g. `<X3><fL4>:01234567890:`
   - Code 39, UPC, EAN, Codabar: no bracketing needed beyond the spec-defined start/stop chars
   - **If delimiters are missing, the parser consumes all subsequent FGL commands as barcode data.** The symptom is a partially-rendered or blank barcode *and* everything after it on the ticket vanishing.
   - `<BC...>` is not an FGL command. If you find it in generated code, replace it with the correct command.
5. **`<X3>` is required at 300 dpi** and must come before the symbology command. Canonical order (hardware-confirmed): **position → expand → symbology → data**: `<RC500,80><X3><oL4>^DATA^`. Without `<X3>`, bars are 1 dot wide and invisible.
6. **Prefer lowercase bar code selects** (`<nL4>`, `<oL4>`, etc.) so rotation commands apply. Uppercase (`<NL4>`) is legacy and ignores `<NR/RR/RU/RL>`.
7. **Rotation changes the anchor corner.** `<RR>` = top of the rotated character is at the column you set; the character builds *down to the right* in its rotated frame. Test with one character before laying out a full rotated panel. Note: `<BX>`, `<VX>`, `<HX>` box/line primitives do **not** rotate — they always draw on the absolute axis.
8. **Scrub printable text** for parser-sensitive characters before placing it in the stream: `<`, `>`, `^`, `:`, `~`. A `<<` mid-text puts the parser into command mode and silently corrupts everything that follows. Replace with safe ASCII (`** TEAR HERE **` not `>> TEAR HERE <<`). **Hard fonts (`<F3>` OCR-B and friends) also lack `[`, `]`, and several punctuation glyphs — they substitute garbage characters like `Ä`, `Ü`. Stick to ASCII alphanumerics + space + colon + dash + period under hard fonts; switch to TrueType (`<TTF>`) for arbitrary text.**
9. **`<HW>` is height-first**: `<HW2,3>` = height×2, width×3. No space between `<HW` and the digits — `<HW 1,1>` is malformed. Default useful size at 300 dpi: `<F3><HW2,2>`.
10. **Inverted text**: `<EI>...<DI>` — always pair them, never leave inversion on across regions or bar codes.
11. **Terminator**: end the file with one of `<p>` (print + cut), `<q>` (print, no cut), `<z>`, `<h>`, or `<r>` (hold-image). The terminator opcodes are lowercase and case-sensitive. See `references/commands.md` and `references/validation.md` (FGL004) for the full set.

12. **Flash-write commands MUST be sent standalone.** `<rte>`, `<rtd>`, `<pl#>`, `<tl#>`, `<dpl>`, `<pf>`, `<tf>`, `<sb>`, `<mb>`, `<xe>`, `<cs>` all write to flash and trigger a 2–3 second printer reset. Any data sent during the reset window is silently dropped — the host reports success but no ticket emerges. **Never embed these in a ticket stream.** They go in their own one-line print job, with a ~3-second delay before the next ticket. See `references/orientation.md` and the "Flash-write hazards" section of `references/commands.md`.

13. **Don't try to invert orientation per-element with `<RU>`.** If you need the layout flipped (perforation on user-view "left"), set `<rte>` once at provisioning and author with the mirror helper. `<RU>` per-region doesn't rotate boxes/lines (they always draw on the absolute axis), so the layout falls apart.

14. **Stub-strip text is HORIZONTAL stacked, NOT rotated.** Despite looking rotated at first glance, ticket-stub text on Broadway-style tickets is short horizontal `<F2>` / `<F3>` strings stacked vertically in a narrow column. Use `<HW2,1>` (height-only scale) to fit narrow stub regions. Don't use `<RR>` per line — it produces "spine of a book" output that's unreadable.

15. **Under `<rte>`, anchor barcodes ≥200 dots from the right safety margin.** Ladder barcodes near the right edge have disappeared entirely on hardware. Prefer picket-fence (`<FP8>`, `<FP10>`) over ladder for vertical-bar appearance in user view.

16. **For UTF-8 / extended characters (€, ä, ö, ü, ß, etc.), prefix with `<TRE><TT4>`.** Without translation enable + UTF-8 mode, multi-byte sequences print as garbage. Older firmware may render extended chars only on `<F13>` (Courier large), not `<F8>` — run both as a smoke test.

After writing the file, run `wc -c <path>` so the user sees the artifact size, and pretty-print the first ~30 lines back with line numbers so the user can audit.

---

## Step 4: Edit an existing layout

When `$ARGUMENTS` is an existing `.fgl`:

1. Read the file. Decompose it back into a region table by parsing `<RC...>` anchors.
2. Show the table to the user with AskUserQuestion:
   ```
   Question: "Which region(s) do you want to change?"
   Options:
     - one option per region from the table
     - "Add a new region"
     - "Other" — free-form
   ```
3. Apply edits with `Edit`, never rewriting the whole file (preserve any user comments that begin with a `;` or are wrapped in `< >` no-op text).
4. Re-validate with the same critical rules from Step 3.

---

## Step 5: Image-only conversion

When `$ARGUMENTS` is an image path:

1. Confirm the image is 1-bit-convertible (BOCA prints black/white only). Show its size in pixels with `file <path>`.
2. Ask the threshold and target dot dimensions:
   ```
   Brief in prose: "I'll threshold the image, pack 8 vertical pixels per byte (MSB top), and emit
                    <RCr,c><g{2N}>HEXHEX... per 8-row strip. The image's pixel size becomes its
                    dot size 1:1 — at 300 dpi, a 200×100 px image prints ~0.66"×0.33"."
   Question: "Convert with which settings?"
   Options:
     - "Threshold 128, no dither, place at RC0,0 (recommended)"
     - "Threshold 128, Floyd–Steinberg dither, RC0,0"
     - "Custom" — ask for threshold, dither, anchor row/col, max width in dots
   ```
3. Run the bundled converter:
   ```bash
   python3 skills/fgl-layout/scripts/png_to_fgl.py \
       --input <image> \
       --threshold 128 \
       --row 0 --col 0 \
       --output thoughts/shared/fgl/<slug>.png-snippet.fgl
   ```
   The script writes ASCII-hex `<g#>` graphics; see `references/image-to-fgl.md` for the exact algorithm and how to wrap the output as a downloadable logo (with `ESC` brackets and `<ID#>`).
4. Offer to splice the snippet into an existing `.fgl` layout at the desired anchor.

---

## Validation

After every Write or Edit of a `.fgl` file, the plugin's `PostToolUse` hook automatically runs `python -m fgl_validator` against the file. Diagnostics surface in the next tool result as `path:line:col: severity: [code] message`. Read them and fix any reported issues before declaring done. The hook is advisory and never blocks the write.

Codes you may see (full descriptions in `references/validation.md`):

- `FGL000` — parse error.
- `FGL001` — unknown opcode (consult `references/opcodes.md` before inventing one).
- `FGL002` — wrong arity for a known opcode.
- `FGL003` — coordinate out of printer bounds (default Lemur 2400×2400).
- `FGL004` — segment missing terminator from `{p, q, z, h, r}`.
- `FGL005` — `<HW>` left non-default at end of segment.
- `FGL006` — ladder barcode ink mass over printer budget (silent-drop hazard; see `references/ink-budget.md`).

In addition, walk this human checklist before reporting done — the validator does not catch every semantic mistake:

- [ ] File begins with no stray bytes before the first `<` command.
- [ ] Every `<RC...>` has a comma between row and column.
- [ ] Every `<EI>` has a matching `<DI>` before any bar code.
- [ ] No region writes outside the canvas (rows 0 to `R-1`, columns 0 to `C-1`, leaving the 14-dot safety border per edge).
- [ ] Bar codes start at a column that leaves room for their full rendered width (per the supplement formulas in `references/commands.md`).
- [ ] File ends with one of `<p>`, `<q>`, `<z>`, `<h>`, or `<r>` and a newline.
- [ ] No flash-write commands (`<rte>`, `<rtd>`, `<pl#>`, etc.) are embedded in the ticket stream.

### Troubleshooting hardware-iteration failures

- **"Silent success" — the print job leaves the queue cleanly but no ticket emerges.** First suspect: a flash-write command (`<rte>`, `<rtd>`, `<pl#>`, `<sb>`, etc.) embedded in the ticket stream. The printer resets, drops the data, and the host reports "ok." Move the config command to a standalone job with a ~3-second wait.
- **Garbage glyphs in printable text (`Ä`, `Ü` instead of `[`, `]`).** Hard fonts have limited character sets. Drop the punctuation or switch to a TrueType font.
- **Barcode missing or rendered as plain text.** Check (a) `<X3>` precedes the symbology command at 300 dpi, (b) data is wrapped in the right delimiter (`^…^` for Code 128, `:…:` for I2of5), and (c) the anchor leaves enough horizontal room from the right safety margin (≥200 dots under `<rte>`, ≥80 dots otherwise).
- **Layout looks fine in `tree.pretty()` but the printed ticket is corrupt downstream of one region.** Almost always a missing barcode delimiter or a `<<`/`>>` in printable text consuming subsequent commands as data.
- **Photos lie.** Lighting, glare, perspective, and shadow obscure detail. The only reliable measurement of a printed ticket is a physical mm ruler laid against it.
- **Enumerate expected vs actual.** When a ticket looks wrong, list every region with its expected (row, col, font, content) and what's actually visible. The bug pattern usually jumps out from the diff.

---

## Bundled Resources

- [`references/commands.md`](references/commands.md) — complete FGL command reference: text, fonts, drawing, bar codes, graphics, status, file mgmt.
- [`references/coordinate-math.md`](references/coordinate-math.md) — dpi → dot conversions, font box sizes, ticket geometry.
- [`references/image-to-fgl.md`](references/image-to-fgl.md) — image conversion algorithm, hex packing, downloadable-logo wrapping.
- [`references/opcodes.md`](references/opcodes.md) — canonical opcode catalog with arities (the validator's `KNOWN_OPCODES`). Use this to avoid `FGL001`/`FGL002`.
- [`references/orientation.md`](references/orientation.md) — `<rte>`/`<rtd>` patterns, the mirror helper for user-view authoring, stub-strip stacking, right-edge clipping under reverse orientation.
- [`references/ink-budget.md`](references/ink-budget.md) — the FGL006 model: per-print ink budget, ladder mass formula (num_bars × OL × 8 × X²), the empirical Lemur cliff at ~45k.
- [`references/variables.md`](references/variables.md) — `<VAn>` runtime variable substitution table for diagnostic / health-check tickets.
- [`references/validation.md`](references/validation.md) — what each `FGL00X` rule checks and how to satisfy it.
- [`templates/basic-ticket.fgl`](templates/basic-ticket.fgl) — minimal scaffold.
- [`templates/event-ticket.fgl`](templates/event-ticket.fgl) — multi-region scaffold (title, seat block, barcode, footer).
- [`scripts/png_to_fgl.py`](scripts/png_to_fgl.py) — image-to-FGL converter (PNG/BMP → `<g#>` hex strips).

## Guidelines

- **Always confirm canvas before laying regions.** A 300-dpi assumption on a 200-dpi printer halves every coordinate.
- **One template, then edit.** Don't synthesize FGL from scratch.
- **Use AskUserQuestion at every decision** (printer, regions, edit targets, image settings). Never assume.
- **Keep the artifact human-readable.** One logical region per line. The FGL parser ignores newlines outside command brackets.
- **Don't transmit.** Skill produces `.fgl`; the user (or a paired sender script they request explicitly) sends to the printer.
- **Out of scope**: RFID tag programming, magnetic stripe encoding, network/WiFi configuration. Point users to the corresponding addenda in the BOCA programming guide.

### Iteration discipline (hardware testing)

When a layout reaches the hardware-test phase, every print is a 1–2 minute round trip — much slower than the software dev loop. Apply these rules:

- **Don't bump everything in one pass.** When a font is too small, double the font; don't simultaneously re-anchor a barcode and change orientation. One- or two-axis changes per print make the next result diagnostic.
- **Read the spec front-to-back before guessing.** Hardware iteration is expensive; a 30-minute spec read often saves five hardware iterations.
- **Photos lie — use a physical ruler.** A mm ruler against the printed ticket is the only reliable measurement.
- **Enumerate expected vs actual.** "What's missing" is at least as informative as "what's there." List every region with its expected (row, col, font, content), then mark what's actually visible.
- **The first sign that a config command is broken is silent success** — the print job leaves cleanly, no error, no ticket. If this happens, suspect a flash-write command in the stream causing a reset.
- **The notes pay for themselves by the third iteration.** Re-read the relevant reference doc (`orientation.md`, `coordinate-math.md`) before each iteration to avoid re-discovering the same gotchas.
