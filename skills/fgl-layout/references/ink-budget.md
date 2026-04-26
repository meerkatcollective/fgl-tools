# Ink Budget — FGL006

The BOCA Lemur appears to have a per-print **render budget** — finite memory or processing capacity for resolving filled-pixel commands within one ticket. When a single barcode requests too many black dots, the printer doesn't refuse the job and doesn't crop the barcode. Instead it **silently drops content elsewhere on the canvas**. Empirically the dropped content is at the opposite corner from the heavy element: a heavy ladder barcode anchored at the right edge causes the left stub and top descriptor rows to vanish, while the barcode itself prints fine.

This is the only known FGL hazard where the symptom appears in a *different region* than the cause. The validator rule **FGL006 `barcode_ink_mass`** flags ladder barcodes whose computed ink mass exceeds the printer profile's `max_ink_mass`.

## Why X² for ladder

`<X#>` multiplies **both dimensions** of every bar in a ladder barcode:

- Each bar grows wider in the print direction (`X` dots wide instead of 1).
- Each bar grows taller in the long axis (because ladder bars run perpendicular to print direction and `X` scales their length too).

So doubling X **quadruples** the ink mass per bar, not just doubles it. That's why even small `<X#>` bumps can push a barcode over the budget cliff.

For **picket-fence** orientations (`<oP#>`, `<nP#>`, etc.), the geometry is different — bars run along the print direction and `X` scales only the bar width, not length. Mass scales linearly in X. The rule deliberately **does not** flag picket-fence barcodes; we don't have hardware-confirmed thresholds for them.

## The mass formula (ladder symbologies)

```
mass = num_bars × bar_height_units × 8 × X²
```

where:

- `num_bars` ≈ symbology-specific function of data length (see table below).
- `bar_height_units` = the integer arg to the select command (`<oL5>` → 5).
- `X` = the value from `<X#>` preceding the select. Defaults to 1 if no `<X#>` is set.

## Empirical data — TKTS booth Lemur

Calibration runs with a **16-character Code 128 ladder** (`<oL#>^16-char-data^`):

| `<X#>` | `<oL#>` | `OL × X²` | Computed mass | Result |
|---|---|---|---|---|
| 3 | 3 | 27 | ~14k | works |
| 5 | 3 | 75 | ~40k | works |
| 4 | 5 | 80 | ~43k | works (ceiling) |
| 4 | 6 | 96 | ~51k | breaks |
| 8 | 3 | 192 | ~103k | breaks badly |

The cliff sits between `OL × X²` of 80 and 96, i.e. between mass of 43k and 51k. The default `LEMUR.max_ink_mass` is **45000**, just below the cliff.

## How to fit a bigger barcode

The rule of thumb is: **more data at the same X** beats **larger X with the same data**. Adding characters increases the bar count linearly, while raising X grows mass quadratically. Examples:

| Geometry | Computed mass | Outcome |
|---|---|---|
| 16 chars, X=4, OL=5 | ~43k | At ceiling |
| 22 chars, X=4, OL=5 | ~59k | Over — would warn |
| 22 chars, X=3, OL=5 | ~33k | Safe and visibly bigger barcode than the original |
| 22 chars, X=3, OL=8 | ~53k | Over — taller bars still cost X²-equivalent |

So if you need a "bigger" barcode, prefer denser data (more characters, same X) rather than larger X.

## Per-symbology bar-count approximations

Calibrated where empirical data exists, otherwise spec-derived:

| Symbology | `num_bars(N)` | Source |
|---|---|---|
| Code 128 | `4*N + 3` | Calibrated against TKTS booth Lemur (X4 OL5 N=16 → 67 bars → 43k mass) |
| Code 39 | `5*N + 10` | Spec-derived (9 modules/char ≈ 5 bars + start/stop overhead) |
| Interleaved 2 of 5 | `2*N + 4` | Spec-derived (5-module pairs, ~2 bars/digit) |
| Codabar | `5*N + 6` | Spec-derived |
| UPC-A | `30` (fixed) | Spec-derived (12-digit fixed format) |
| EAN-13 | `30` (fixed) | Spec-derived |

If you have empirical mass measurements for a non-Code-128 symbology, recalibrate the constant in `src/fgl_validator/rule_set.py:LADDER_SYMBOLOGIES`.

## Per-printer-profile thresholds

The threshold lives on `PrinterProfile.max_ink_mass`:

- **Lemur**: 45000 (calibrated)
- **Lemur-K**: 45000 (unverified — same as Lemur until measured on hardware)
- **FGL46**: 90000 (placeholder — larger printer, presumably larger budget)

The rule is severity `warning`, not `error` — the cliff is hardware-specific and we don't want to hard-fail FGL that another printer might handle.

## What this rule does NOT cover (yet)

The ink budget is a property of *all* dark-pixel-emitting commands on the ticket, not just barcodes. In principle:

- Solid boxes (`<BX r,c>`)
- Filled lines (`<HX>`, `<VX>` with `<LT n>` thickness)
- Inverted-print regions (`<EI>...<DI>`)
- Graphics blocks (`<G#>`, `<g#>`, `<LD#>`, `<LO#>`)

…all draw down on the same budget. The rule currently models barcodes only because that's where the empirical hazard has been observed. If a layout exceeds the budget through other geometry, the validator will not flag it.

A useful future extension is a "total-ink-mass" rule that sums every dark-pixel source across the segment. Defer until there's empirical evidence the non-barcode contributors actually trip the budget.
