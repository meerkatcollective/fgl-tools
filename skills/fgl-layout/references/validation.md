# Validation Rules

The plugin's `PostToolUse` hook runs `python -m fgl_validator` against any `.fgl` file you Write or Edit. The validator emits LSP-shape diagnostics:

```
path:line:col: severity: [code] message
```

Source of truth: `src/fgl_validator/rule_set.py`. Keep this file in sync when rules are added or changed.

## FGL000 — Parse error

The Lark LALR parser failed to parse the file. Common causes:

- A literal `<` appearing inside text (it always starts a command). Replace with safe ASCII.
- A `>` without a matching `<`.
- A barcode delimited by `:` that contains whitespace or another `:`.

To avoid: stick to the templates in `templates/`, scrub user-supplied text, and never embed `<`, `>`, `:` in printable strings.

## FGL001 — Unknown opcode

The opcode (e.g. `<ZZ>`) is not in `KNOWN_OPCODES`. Consult `references/opcodes.md` before inventing one.

Note: opcodes are case-sensitive. `RC` ≠ `rc`. Lowercase opcodes are limited to the terminator set (`p`, `q`, `z`, `h`, `r`) plus `t`, `n`, `g`.

## FGL002 — Wrong arity

The opcode is known but received the wrong number of integer arguments. E.g. `<RC10>` fires this because `RC` requires 2 args.

Argument count for every opcode is in `references/opcodes.md`.

## FGL003 — Coordinate out of bounds

`<RC r,c>` referenced a coordinate outside the active printer profile's `max_y × max_x`. Default profile (Lemur) is 2400×2400 dots.

To avoid: confirm dpi and ticket size in Step 1 of the skill workflow, then keep all `<RC>` anchors within the computed canvas.

## FGL004 — Missing terminator

A segment did not end with a terminator opcode from `{p, q, z, h, r}`. The validator splits multi-ticket streams on these terminators, then validates each segment — every segment must terminate.

To avoid: always end a layout with `<p>` (or one of the alternates). For multi-ticket streams, every ticket gets its own terminator.

## FGL005 — `<HW>` left non-default (warning)

`<HW>` is global state that persists until reset. This warning fires when:

1. The ticket explicitly resets HW to the default `<HW6,6>` at least once (proving inline use), AND
2. HW is changed to a non-default value, AND
3. The terminator is reached without a final reset.

Tickets that just set a non-default HW once at the top as a global setting are allowed and do not trigger this rule.

To avoid: pair `<HW2,2>` … `<HW6,6>` blocks for any inline size change.

---

## How to read the diagnostics

Every diagnostic is sorted stably by `(line, col, code)`. Severity is `error` for FGL000–FGL004 and `warning` for FGL005. The CLI exits 1 if any error-severity diagnostic is present and 0 otherwise; the plugin hook respects that.
