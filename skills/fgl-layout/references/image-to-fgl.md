# Image → FGL graphics

Source: BOCA programming guide pages 37–40, plus the rsmck.co.uk implementation note (`https://rsmck.co.uk/blog/boca-image/`). The blog confirms that `.bmp`/`.pcx` modes are flaky on older MiniMB heads — converting to native FGL `<g#>` ASCII-hex is the most reliable path.

## Algorithm

1. **Threshold.** BOCA prints black or white only. For input `img` (greyscale or RGB):
   - Convert to greyscale.
   - For each pixel, output `1` (black dot) if `luminance < threshold` else `0`. Default threshold = 128.
   - Optional: apply Floyd–Steinberg dither before threshold for photo-like inputs.
2. **Crop / pad height to a multiple of 8.** FGL packs 8 vertical pixels per byte. If your image is 100 px tall, pad to 104.
3. **Pack column-major, MSB top.** For each column `c` and each 8-row strip `s` (top strip = `s=0`):
   ```
   byte = 0
   for bit_in_strip in 0..7:
       y = s*8 + bit_in_strip
       if pixel[y][c] is black:
           byte |= (1 << (7 - bit_in_strip))
   ```
4. **Emit one strip at a time.** For strip `s` at canvas anchor `(row0, col0)`:
   ```
   <RC{row0 + s*8},{col0}><g{2*W}>HEX0HEX1...HEX{W-1}
   ```
   where `W` = image width in columns and each `HEXi` is two ASCII hex chars (uppercase, leading zero).
5. **Repeat for every strip** until the image is consumed.

## Why ASCII hex (`<g#>`) instead of binary (`<G#>`)

- `<G#>` sends bytes 0–255 raw. If the data contains `0x3C` (`<`), some hosts (particularly Windows print spoolers, AS400 transforms) interpret it as a command bracket and corrupt the stream.
- `<g#>` sends pure printable ASCII. The number after `g` is `2 × byte_count` (always even).

## Storing as a downloadable logo

To store the image once and reprint it many times, wrap the converted strips in `ESC` (0x1B) brackets and prefix with an ID assignment:

```
<ID3>           # next download = logo #3
ESC             # 0x1B (single byte, NOT the literal "ESC")
<RC0,0><g{2W}>HEX...
<RC8,0><g{2W}>HEX...
<RC16,0><g{2W}>HEX...
...
ESC             # close download
```

Subsequent prints just send `<SP{r},{c}><LD3><p>` to position and print.

For the FGL TEXT LOGO (macro) form, you can store an arbitrary FGL command string the same way — bracketed with `ESC` characters — and replay it via `<LD#>`. Restrictions: no `<G>` or `<LD>` inside the macro; first character after the opening `ESC` must be `<`.

## Using the bundled converter

```
python3 skills/fgl-layout/scripts/png_to_fgl.py \
    --input path/to/logo.png \
    --threshold 128 \
    --row 0 --col 0 \
    --output thoughts/shared/fgl/logo-snippet.fgl
```

Flags:
- `--input` — PNG, BMP, or TIFF path.
- `--threshold N` — 0–255, default 128.
- `--dither` — apply Floyd–Steinberg before threshold.
- `--max-width N` — resize so width fits in N dots (preserving aspect).
- `--row R --col C` — anchor for the top-left strip.
- `--logo-id N` — wrap output as a downloadable logo (`<ID N>` + `ESC` brackets).
- `--validate file.fgl` — lint mode: bracket balance, anchor-bounds check, common pitfalls.
- `--output PATH` — defaults to stdout.

The script depends on `Pillow`. If unavailable, the user can `pip install pillow` (or use the system package manager). If Pillow is missing, the script prints a one-line install hint and exits non-zero.

## Sizing example

A 1" round logo at 300 dpi → 300 × 300 pixels (must be 1-bit thresholded). After packing, 300 strips of `2 × 300 = 600` hex chars each. Expect ~180 KB of FGL text per such logo. The FGL46 Lemur has up to 28 MB of download space, so this is ample.

## Pitfalls observed in the rsmck.co.uk write-up

1. **PCX is described as "flaky or slow" on older MiniMB heads.** Use native `<g#>` for portability.
2. **Don't use `print_r`-style debug output.** Stray newlines between strips cause the `<g#>` byte count to be wrong by exactly the number of inserted whitespace characters.
3. **Always specify the count `#`.** `<G>` (no count) defaults to exactly 7 bytes. Drop one byte and the next byte is interpreted as a command character.
