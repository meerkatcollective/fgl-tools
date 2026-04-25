# FGL Command Reference

Source: TLS-Boca Systems FGL Programming Guide, Rev 12 (Feb 2020). Commands are case-sensitive; uppercase and lowercase variants are *different commands*. Lowercase commands often store state in flash and should be used sparingly.

## Conventions

- All commands are wrapped in `< >`.
- Numeric parameters are ASCII digits, not raw bytes (`<RC10,30>` sends '1','0',',','3','0').
- Commands may be concatenated with no whitespace between: `<F2><HW2,2><RC60,300>HELLO`.
- Text outside `< >` is printed.
- Default state at start of every ticket: `<F3>`, `<NR>`, `<HW1,1>`, `<BS21,34>`, cursor (0,0).

## Cursor & geometry

| Command | Effect |
|---|---|
| `<RCr,c>` | Move cursor to row `r`, column `c`. **Required** before each region. |
| `<NR>` | No rotation (default). Builds down-and-right from anchor. |
| `<RR>` | Rotate +90° (right). Anchor is top-right of the rotated glyph in printed orientation. |
| `<RU>` | Rotate +180° (upside down). |
| `<RL>` | Rotate -90° / +270° (left). |

## Sizing

| Command | Effect |
|---|---|
| `<HWh,w>` | Height multiplier `h`, width multiplier `w` — **height is first**. Spec: `<HW2,3>` → height=2, width=3. Cap = 16 for soft fonts. Reset with `<HW1,1>`. **No space** between `<HW` and the digits — `<HW 1,1>` is malformed. |
| `<BSw,h>` | Box size: width `w`, height `h` (**width first** — opposite of `<HW>`). Default 21×34 for `<F3>`. Affects inter-character spacing. |
| `<X#>` | Bar-code bar-width multiplier (1–9). `<X2>` recommended for 200 dpi, `<X3>` for 300 dpi. |

## Resident fonts (standard heads)

| Command | Font | Cell (W×H) |
|---|---|---|
| `<F1>` | Tiny | 5×7 (illegible at 300 dpi without `<HW3,3>` or larger) |
| `<F2>` | Headline | 8×16 |
| `<F3>` | Default | 17×31 |
| `<F4>` | OCRA small | 5×9 |
| `<F6>` | Large OCRB | 30×52 |
| `<F7>` | OCRA | 15×29 |
| `<F8>` | Courier | 20×40 (or 20×33) |
| `<F9>` | Small OCRB | 13×20 |
| `<F10>` | Prestige | 25×41 |
| `<F11>` | Script | 25×49 |
| `<F12>` | Orator | 46×91 |
| `<F13>` | Courier | 20×40 (or 20×42) |

TrueType (FGL46 / Lemur / 26 / some 24/44):
- `<TTF#,pt>` — select TrueType font ID `#` at point size `pt`.
- `<ttf#>` followed by binary file — download a TTF.
- `<TTCP#>` / `<ttcp#>` — select code page.

## Drawing

| Command | Effect |
|---|---|
| `<BXr,c>` | Draw box `r` rows tall × `c` cols wide from cursor. |
| `<VXr>` | Vertical line, 1 dot wide, `r` rows long (draws down from cursor). |
| `<HXc>` | Horizontal line, 1 dot tall, `c` cols long (draws right from cursor). |
| `<LT#>` | Set thickness for the **next** line/box (resets to 1 after). Re-issue per shape. |

**Note**: boxes and lines do **not** respect `<RR>` / `<RU>` / `<RL>` rotation. They always draw relative to the absolute axis regardless of current rotation state. If you need a rotated frame, use explicit coordinates.

## Bar codes (1-D)

Two select forms:
- **Old** (uppercase, ignores rotation): `<NL5>123456`, `<UL5>...`, `<EL5>...`, `<FL5>...`, `<CL5>...`, `<OL5>...`
- **New** (lowercase, respects current `<NR/RR/RU/RL>`): `<nL5>`, `<eL5>`, `<nP5>` (picket fence), etc.

Letter map: `n`=Code39, `u`=UPC, `e`=EAN-13/8, `f`=Interleaved 2 of 5, `c`=USS-Codabar, `o`=Code 128, `s`=Softstrip.
Orientation: `L`=ladder, `P`=picket-fence.
Number after letter = bar height in 8-dot units (default 4 → 32 dots).

**Canonical barcode form** (hardware-confirmed): position → expand → symbology → data:
```
<RC500,80><X3><oL4>^BARCODE-DATA^
```

### Data bracketing by symbology — REQUIRED, not optional

| Symbology | Command form | Data format | Example |
|---|---|---|---|
| Code 39 | `<nL4>` / `<NL4>` | Plain string; `*` optional start/stop | `<RC...><X3><nL4>ABC123` |
| Interleaved 2 of 5 | `<fL4>` / `<FL4>` | **Colon-delimited** `:DATA:` (even digit count) | `<RC...><X3><fL4>:0123456789:` |
| Code 128 | `<oL4>` / `<OL4>` | **Caret-delimited** `^DATA^` | `<RC...><X3><oL4>^ABC123^` |
| UPC-A | `<uL4>` / `<UL4>` | 11-digit string (check digit added) | `<RC...><X3><uL4>07200000042` |
| EAN-13 | `<eL4>` / `<EL4>` | 12-digit string | `<RC...><X3><eL4>123456789012` |
| USS-Codabar | `<cL4>` / `<CL4>` | Start/stop char + digits | `<RC...><X3><cL4>A12345B` |
| QR Code | `<QRV2>` / `<QRV7>` etc. | **Curly-brace-delimited** `{DATA}` | `<RC...><QRV7>{https://example.com}` |

**Critical**: If the data delimiters are wrong, the printer consumes subsequent commands as barcode data, silently corrupting everything that follows on the ticket.

### Bar width and DPI

`<X#>` (1–9) multiplies bar width in dots. Place it **between** the select command and the data string. Without it, bars default to 1 dot wide.

| DPI | Minimum usable | Recommended |
|---|---|---|
| 200 | `<X2>` | `<X2>` |
| 300 | `<X3>` | `<X3>` |
| 600 | `<X1>` | `<X2>` |

At 300 dpi without `<X3>`, bars are one dot (≈0.003") wide — effectively invisible in print.

| Command | Effect |
|---|---|
| `<BI>` | Add human-readable interpretation under the next bar code. |
| `<X#>` | Bar width multiplier — place after select, before data. See table above. |
| `<NXL5>str` / `<NYL5>str` | 3:1 ratio Code 39 / I2of5. |

## 2-D bar codes (FGL46+)

| Command | Effect |
|---|---|
| `<PDF417,...>data<p>` | PDF-417. |
| `<DM#,...>data<p>` | Data Matrix. |
| `<QRV2>` / `<QRV7>` / `<QRV11>` / `<QRV15>` | QR Code versions. |
| `<AZ...>data<p>` | Aztec. |

See the *Two Dimensional Bar Code Supplement* for parameter formats.

## Inverted print

| Command | Effect |
|---|---|
| `<EI>` | Enable inverted (white-on-black). Adds a black border around each glyph. |
| `<DI>` | Disable inverted. **Always pair before any bar code.** |

## Graphics (raw bitmap)

| Command | Effect |
|---|---|
| `<G>byte1,...,byte7` | 7 bytes of dot data (8-bit) starting at cursor. |
| `<G#>byte1,byte2,...,byte#` | `#` bytes of dot data, raw 8-bit. No commas — bytes are sent as raw 0–255 values. |
| `<g#>HEXHEX...` | ASCII-hex variant. `#` = **2 ×** byte count. Each pair of hex chars = one byte. |

Each byte = 8 vertical dots in one column, MSB on top. After 8 rows, increment the row by 8 and re-issue `<RC...>` (or `CR` to drop down a strip).

## Logos & files

| Command | Effect |
|---|---|
| `<SP r, c>` | Starting point for the next logo (analog of `<RC>` for logos only). |
| `<LO#>` | Print resident factory logo `#`. |
| `<LD#>` | Print downloaded logo `#`. |
| `<ID#>` | Assign next-downloaded file's ID. |
| `<DF#>` | Delete file. (1=all perm+temp, 7=soft font by ID, 8=logo by ID, 9=defrag flash.) |
| `<PF>` / `<TF>` | Default mode = permanent / temporary. |
| `<SF#>` | Print soft font `#`. |

## Print termination

| Command | Effect |
|---|---|
| `<p>` | Print + cut. Preferred over `FF`. |
| `<q>` | Print, no cut. |
| `<z>` | Print + eject. |
| `<h>` | Print, hold image (for chained tickets). |
| `<r>` | Print, no cut, hold image. |
| `<FF>` (0x0C) | Legacy print + cut. Some hosts strip 0x0C — prefer `<p>`. |

## Status

| Command | Effect |
|---|---|
| `<S1>` | Status request. |
| `<S2>` | Firmware + ticket count. |
| `<S7>` | Free download bytes. |
| `<S8>` | Partial ASCII status. |
| `<ME>` / `<MD>` | Enable / disable CRT messages. |

## Permanent printing length

| Command | Effect |
|---|---|
| `<PL#>` | Set ticket print length (dot columns) for this session. |
| `<pl#>` | Permanent — store in flash. |
| `<tl#>` | Permanent ticket length (for label stock with gaps). |
| `<dpl>` | Re-enable auto-measure (delete `<pl>`/`<tl>`). |

## Common pitfalls

1. **No comma in `<RC>`** → all data after that point is silently dropped.
2. **Forgetting to re-issue `<LT#>`** → only the first box has the intended thickness.
3. **Bar code under inverted mode** → ignored; always `<DI>` first.
4. **Old-style bar code with `<RR>`** → orientation does not change; switch to lowercase `<nL5>` etc.
5. **Sending `<FF>` (0x0C) over a host that strips control characters** → ticket never prints; use `<p>`.
6. **Image bytes via `<G#>` containing the ASCII for `<` (0x3C)** → printer can mis-frame the next command if exactly 7 bytes follow `<G>` without count. Always specify `#`.
7. **Missing Code 128 carets** (`<oL4>MYDATA` instead of `<oL4>^MYDATA^`) → parser treats everything after the command as barcode data, consuming subsequent FGL commands as literal characters until it times out. Symptoms: barcode renders partial or blank; text/graphics *after* the barcode disappear.
8. **Missing I2of5 colons** (`<fL4>1234` instead of `<fL4>:1234:`) → same runaway-data issue as above for Interleaved 2 of 5.
9. **No `<X3>` at 300 dpi** → bars are 1 dot (≈0.003") wide, invisible in print. Data may print as text instead of a scannable bar code.
10. **`<BC...>` is not an FGL command.** There is no `<BC>` in the spec. Unrecognised commands are ignored and the raw text (e.g. `<BC3,2,0,32>`) may be printed literally — the classic sign that the data printed as plain digits instead of a barcode.
11. **`<rte>` is not "real-time enable".** It is the **Orientation Reverse** command — a flash-stored config command that permanently rotates the printer's output 180°. Its sibling `<rtd>` restores the default orientation.
    - **Flash-stored config commands (including `<rte>`) trigger a 2–3 second printer reset.** Any data sent during the reset window is silently discarded. QZ Tray / the host reports "success" because bytes were transmitted; the printer never received them.
    - **`<rte>` must be sent standalone** in its own print job. Wait ~3 seconds before sending ticket data. Never embed it in the same FGL stream as layout content.
    - The reset hazard applies to all lowercase flash commands (`<pf>`, `<tf>`, `<pl#>`, `<tl#>`, etc.) — all of them are one-time configuration, not per-ticket commands.
12. **`<` and `>` in printable text** confuse the FGL parser. `<<` mid-text causes the parser to enter command mode and consume the next legitimate command as garbage parameters. Likewise `>>`. Scrub printable strings for: `<`, `>`, `^` (Code 128 delimiter), `:` (I2of5 delimiter), `~` (special char prefix). Replace with safe ASCII (e.g., `** TEAR HERE **` not `>> TEAR HERE <<`).
13. **`<HW 1,1>` with a space is malformed.** The spec form is `<HW1,1>` — no space between `HW` and the digits. A space causes the command to be ignored and may cascade into layout corruption.
