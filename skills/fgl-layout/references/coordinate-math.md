# Coordinate Math

FGL ticket area is a fixed dot grid. All positioning is integer rows/columns.

## DPI → dot size

| DPI label | Dot size | Real dpi |
|---|---|---|
| 200 | .00492" | 203.2 |
| 300 | .00328" | 304.9 |
| 600 | .0015" | 600 |

Position `(0,0)` = top-left of the ticket as it ejects (default orientation).

**Axis mnemonic** — the print head fires across the **short** axis of the ticket:
- **ROW = short axis** (perpendicular to feed direction, max ~600 dots on a 2" wide stock @ 300 dpi)
- **COL = long axis** (along feed direction, max ~1650 dots on a 5.5" stock @ 300 dpi)

Getting ROW and COL transposed is the most common coordinate bug. When in doubt: rows count across the narrow width, columns count along the long length.

## Common canvas sizes

| Ticket | DPI | Rows × Cols (usable area) |
|---|---|---|
| 2" × 5.5" | 200 | 384 × ~1050 (≈1077 absolute, leave last 29 cols clear) |
| 2" × 5.5" | 300 | 600 × ~1650 |
| 2" × 7" | 200 | 384 × ~1340 |
| 4" × 6" (label) | 200 | ~768 × ~1180 |
| 4" × 6" (label) | 300 | ~1150 × ~1770 |

The guide notes you should avoid printing in the **last 2–3 dot columns** because measured ticket length varies slightly between black-mark stops. In practice on the Lemur @ 300 dpi, content past **col ~1500** has been observed to clip intermittently — treat 1500 as the practical right edge until verified with `<dpl>` + power-cycle re-measure on your specific stock.

## Safety border

BOCA reserves ~14 dots inside each edge. Treat usable area as:
- rows: `[14, R-14]`
- cols: `[14, C-14]`

Any data outside this band may be clipped depending on registration.

## Font box footprint

For default `<F3>` (17×31) with default `<BS21,34>`:
- Each non-rotated character occupies 21 columns × 34 rows starting at `<RC>`.
- Line height = 34 rows; column advance per char = 21.

For sized text `<HWh,w>` (height first, width second):
- Effective box = `21*w` cols × `34*h` rows (where `h` = first param, `w` = second param).

When you switch to `<F2>` (8×16) with default `<BS>`, the 21×34 box still applies — characters are top-left justified within it. To tighten, send `<BS10,18>` after `<F2>`.

## Rotation effects

Each rotation re-anchors:
- `<NR>` — text builds **down + right** from `<RC>`. Anchor = top-left.
- `<RR>` — text builds **right + down** in printed orientation, but in glyph space it's "down + right" rotated +90°. Anchor = top-right of the rotated character. To start a `<RR>` line at row 200, col 100 and have it read top-to-bottom on the right side of the ticket, set `<RC200,100>` then `<RR>...`.
- `<RU>` — anchor = bottom-right.
- `<RL>` — anchor = bottom-left.

Rule of thumb: when in doubt, print one character at the anchor first, see where it lands, then lay out the rest.

## Bar code width math

For a ladder Code 39 bar code at default `<X1>`:
- Each "unit" of the size parameter = 8 dots high.
- A picket-fence Code 39 string `S` of length `L` is roughly `(L * 16 + 35)` dots wide at default ratio; allow margin.
- After expanding via `<X2>` or `<X3>`, multiply width by that factor.

Always start a bar code with at least 50 dots of clearance on the leading and trailing edges so the human-readable interpretation (`<BI>`) has room.

## Recommended grid for 2"×5.5" @ 300 dpi

```
rows 0..14         → top safety border
rows 15..120       → header band (logo / venue)
rows 121..240      → title band (large text)
rows 241..360      → seat block / details (mid)
rows 361..480      → fine print / event date
rows 481..585      → bar code band
rows 586..600      → bottom safety border

cols 0..14         → left safety border
cols 15..1499      → printable (safe on hardware; 1500–1635 intermittently clips on Lemur stock)
cols 1500..1635    → theoretically printable per spec; verify on your hardware before using
cols 1636..1650    → right safety border
```

Use this as a starting point for the region table in Step 2 of SKILL.md.

## Stock-specific notes (2"×5.5" thermal, BOCA Lemur)

- **Stub strip**: the perforation on this stock sits ~128 mm from the leading edge, giving a stub of ~12 mm. Don't assume the generic 25 mm figure from older Boca docs. Stub fields should be designed for the actual 12 mm (~115 dot-column) stub width.
- **Safe col ceiling**: empirically ~1500. The spec allows up to ~1635 but clipping at col 1500+ has been observed on hardware. Design to col 1500 unless you've confirmed otherwise with a ruler against a printed test ticket.
