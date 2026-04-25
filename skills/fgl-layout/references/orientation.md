# Orientation: `<rte>` / `<rtd>` and authoring under flipped coordinates

Boca FGL is a positional language with a fixed coordinate origin: `<RC0,0>` is whatever corner the print head considers top-left in the printer's *current* orientation. For some stocks (perforation on the wrong end relative to the layout you want to author), you need to flip the printer's orientation **once at provisioning time**, then design the ticket from a "user view" perspective with a coordinate mirror in code.

This document captures the orientation patterns we worked out while building the on-prem TKTS booth debug ticket for a 2"×5.5" Lemur. The lessons translate to any 300-dpi Lemur stock where the perforation should land on the "left" of the ticket as a user reads it.

## `<rte>` is *Orientation Reverse*, not "real-time enable"

Earlier internal docs mislabelled `<rte>` as "real-time enable." The Rev 14 spec is unambiguous: it is **Orientation Reverse** — a flash-stored config command that permanently rotates the printer's output 180°. Its sibling `<rtd>` is **Orientation Default**.

Per spec §"Printer Models (adjustable vs. fixed and reverse adjustable)" line 4106:

> "an adjustable FGL printer operating in portrait mode **requires** an `<rte>` command in order to properly format the ticket. This command only needs to be sent once as it is permanently stored in the printer's memory."

So on adjustable models like the BR46 Lemur, `<rte>` is not optional — it's part of provisioning, the same way you would configure paper size or speed.

## Critical: `<rte>` triggers a 2–3 second printer reset

Flash-stored config commands cause the printer to reset (clear buffers, reload settings). **Any data sent during the reset window is silently discarded.** The host (QZ Tray, raw printing, CUPS) reports "success" because the bytes were transmitted; the printer never received them.

This produces the hardest debug failure in FGL: **silent success**. The print job leaves the queue clean, no error pops, but no ticket emerges.

The rule:

- **`<rte>` and `<rtd>` must be sent in their own standalone print job**, never embedded in a ticket stream.
- Wait ~3 seconds before sending the next print job.
- Same goes for the entire flash-command family: `<pl#>`, `<tl#>`, `<dpl>`, `<pf>`, `<tf>`, `<sb>`, `<mb>`, `<xe>`, `<cs>`. All of them are one-time provisioning, not per-ticket commands.
- The spec text says `<rte>` "only works in conjunction with the Boca print driver" — in practice it works fine via QZ Tray's generic Windows raw driver too.

A reasonable provisioning UX is two buttons (`Set Reverse Orientation`, `Set Default Orientation`) on a printer-settings page that fire `<rte>` / `<rtd>` standalone.

## Authoring under `<rte>`: the mirror helper

Once `<rte>` is set, the printer's coordinate system is rotated 180°. To author the layout from a "perforation on the LEFT, top-left origin" user-view, mirror every position before emitting:

```javascript
const ROW_MAX = 600;          // 2" @ 300 dpi
const COL_MAX = 1650;         // 5.5" @ 300 dpi
const rc = (userRow, userCol) =>
    `<RC${ROW_MAX - userRow},${COL_MAX - userCol}>`;
```

This makes user-view `(0,0)` the top-left of the laid-flat ticket. Author every region in user-view coordinates and let the helper translate.

### The line-direction wrinkle

`<HX>` and `<VX>` always draw rightward / downward in *printer* frame, not user frame. Under the 180° flip that means they draw leftward / upward in user view. To anchor a horizontal line of length `L` in user-view coordinates, anchor it at the **far end** in user view:

```javascript
const hLine = (userRow, userCol, len) => `${rc(userRow, userCol + len)}<HX${len}>`;
const vLine = (userRow, userCol, len) => `${rc(userRow + len, userCol)}<VX${len}>`;
```

Always smoke-test with one short line at a known position before laying out a full ticket.

## Don't try to invert with per-element `<RU>`

Tempting alternative: leave the printer in default orientation and per-region apply `<RU>` (rotate 180°) to flip text. **Don't.** Two reasons:

1. `<BX>`, `<HX>`, `<VX>` (boxes, lines) **do not respect** rotation commands — they always draw on the absolute axis. So your text rotates but your frames don't, and the whole layout falls apart.
2. Coordinate math for `<RU>` text re-anchors at the bottom-right corner of each glyph. Combining that with mirrored region geometry is fiddly and error-prone.

The right answer is `<rte>` once at provisioning, then design the layout in user-view coordinates with the mirror helper.

## Stub-strip text is HORIZONTAL, not rotated

A common pattern on Broadway-style ticket stubs is a narrow column of small label/value rows along one short edge. At first glance the text looks rotated 90°, but in practice **the BOCA stubs print short horizontal lines stacked vertically in a narrow column**, not rotated text.

We initially used `<RR>` per line on the stub strip and got "spine of a book" output that was completely unreadable. Removing the `<RR>` and stacking short horizontal `<F2>` / `<F3>` strings in the 22 mm stub strip is correct.

The `<HW2,1>` height-only-scale trick is the win for narrow stub regions: 2× tall, 1× wide so the text still fits in 22 mm of column width.

## Right-edge clipping under `<rte>` — anchor barcodes generously

Two things conspire at the right edge:

1. The Lemur's auto-measured ticket length is sometimes 100+ dots short of the spec maximum, so content past col ~1500 has been observed to clip intermittently (see `coordinate-math.md`).
2. Under `<rte>`, the right edge in user view is the original left edge in printer frame, where the print head's leading dots are slightly less reliable on this stock.

Practical rules for barcodes under `<rte>`:

- Anchor barcodes **at least 200 dots from the right safety margin** in user view.
- Prefer **picket-fence** form (`<FP8>`, `<FP10>`) over **ladder** for vertical-bar appearance — ladder barcodes anchored within ~80 dots of the right margin produced no barcode at all in our tests.
- Always smoke-test a barcode placement on hardware before committing — the spec diagrams assume default orientation, not `<rte>`.

## The provisioning flow

1. Send `<rte>` standalone. Wait 3 seconds.
2. (Optional) print a diagnostic ticket using `<VAn>` substitutions to confirm the printer is responsive after the reset (see `references/variables.md`).
3. Now iterate on real tickets, with the mirror helper applied.

To revert: send `<rtd>` standalone. Wait 3 seconds.

## Spec citation

Boca FGL46 Programming Guide, Rev 14 (Feb 2022) — `<rte>` and `<rtd>` are documented in the §"Printer Models (adjustable vs. fixed and reverse adjustable)" section. URL: https://bocasystems.com/documents/FGL46_rev14.pdf
