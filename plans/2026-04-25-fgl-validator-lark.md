---
date: 2026-04-25
branch: main
commit: aae725e
repository: fgl-tools
source: /Users/willclark/Downloads/fgl-validator-lark.md
---

# FGL Validator (Lark-based) Implementation Plan

## Overview

Build a Python validator for Boca FGL (Friendly Ghost Language) ticket markup using a Lark LALR parser plus a rule-based linter. Output LSP-shape diagnostics. The reference doc (`fgl-validator-lark.md`) is the design spec; this plan stages it into phases each gated by executable tests.

## Current State Analysis

- Fresh repo. Single commit (`aae725e Initial commit`). Only contents: `.claude/`, `CLAUDE.md`.
- No Python project, no `pyproject.toml`, no test harness.
- No existing FGL code in this repo. Reference doc owns all design choices.
- No BDD / outside-in test harness in place — the spec-first gate (Step 3.5) does **not** apply. The pytest fixture corpus described in the doc is our executable specification surrogate; it lands in Phase 3 (the earliest phase with enough plumbing to run rules end-to-end).

## Desired End State

A working `fgl_validator` package that:

1. Parses FGL with `lark` LALR (`fgl.lark`).
2. Transforms to a flat `list[Node]` of `Command | Barcode | Text` dataclasses with line/col.
3. Runs a registered list of rule functions producing sorted `Diagnostic` records (LSP-shape: `code`, `severity`, `message`, `line`, `col`).
4. Ships an MVP rule set: `FGL000` (parse error), `FGL001` (unknown opcode), `FGL002` (wrong arity), `FGL003` (RC out of bounds), `FGL004` (missing `<p>`), `FGL005` (HW left non-default).
5. Has a fixture corpus (`tests/fixtures/{valid,invalid}/`) with at least the Jersey Boys example in `valid/` and one fixture per invalid rule code.
6. Has a CLI (`python -m fgl_validator <path>`) producing `path:line:col: severity: [code] message` lines and exit code 1 on any error.
7. Splits multi-ticket streams on `<p>` and validates each segment.
8. Supports per-printer-profile coordinate bounds (Lemur default 2400×2400, configurable).

Verification: `pytest` is green; `python -m fgl_validator tests/fixtures/valid/jersey_boys.fgl` exits 0; `python -m fgl_validator tests/fixtures/invalid/missing_print.fgl` exits 1 and prints `[FGL004]`.

### Key Discoveries

- Reference doc: `/Users/willclark/Downloads/fgl-validator-lark.md`
  - Grammar boundaries (`fgl-validator-lark.md:25-45`) — `OPCODE` is letters-only so `<F3>` parses as opcode `F` arg `3`.
  - `propagate_positions=True` non-negotiable (`fgl-validator-lark.md:58-61`).
  - Whitespace inside `TEXT` is significant — never `%ignore WS` (`fgl-validator-lark.md:298`).
  - Coordinate bounds are printer-model-specific (`fgl-validator-lark.md:303`).
  - Multi-ticket streams: split on `<p>` and validate each segment (`fgl-validator-lark.md:304`).
- BOCA cheat sheet (committed at `tests/fixtures/.cache/gist.json` via `gh api gists/dba5496db94082d22475953a3cd32a1c`) — owns the **canonical opcode list and arities** that drive `KNOWN_OPCODES`. The reference doc only sketches a handful; the cheat sheet is authoritative.
- Real fixtures (`tests/fixtures/valid/`):
  - `cfg_dump.fgl` — printer config dump, uses `<F3>`, `<RC#,#>`, `<VA#>` × 22, terminator `<p>`.
  - `euro_chars.fgl` — non-ASCII text bytes (`€ ä ö ü ß`); two tickets in one stream, both ending `<p>`.
  - `jersey_boys_ttf.fgl` / `jersey_boys_rtf.fgl` — full ticket layouts using `<TTF8,10>` / `<RTF7,10>`, `<HW#,#>`, `<X4>`, barcode `:902141530292:`. Terminators are `<q>` / `<p>` respectively.
  - `jersey_boys_q_terminator.fgl` — terminator is `<q>`, **not** `<p>`. Real-world proof that the terminator set is broader than the reference doc claimed.
- **Terminator set is `{p, q, z, h, r}`** (cheat-sheet rows for print/eject/hold/no-cut variants), all lowercase. The reference doc's "lowercase `<p>` is the single exception" is *almost* right — it's actually a small lowercase set. `FGL004` broadens accordingly.
- `<p>` lowercase still holds: opcode names are case-sensitive — `RC` ≠ `rc`, and the lowercase opcodes are the terminator group plus `t`/`n` (transparent mode) and `g` (ASCII graphics).
- `<VA#>` is a runtime variable substitution (`<VA1>` … `<VA113>` etc.). Statically we treat it as opcode `VA` with one integer arg; we don't know which variable indices exist, so don't constrain the value.

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Package manager / runner | `uv` | Fast, single-tool, drives `pyproject.toml`; matches modern Python defaults. |
| Python version | `>=3.10` | Doc requires it for `Node = Command \| Barcode \| Text` PEP 604 union and `match` if added later. |
| Project layout | `src/fgl_validator/` | Avoids accidental imports of in-tree files; standard for distributable packages. |
| Parser | Lark LALR | Doc-prescribed; FGL is unambiguous and LALR is fast. |
| Diagnostic shape | LSP minimum (`code`, `severity`, `message`, `line`, `col`) | Universal interchange; trivial to convert to other formats. |
| Rule registration | Module-level decorator + list | Doc-prescribed; resists premature framework. |
| Opcode whitelist source | Inline Python dict (`KNOWN_OPCODES`) seeded from the BOCA cheat sheet (gist `readme.md`) | Keeps the validator a single small file; externalize only when rule disables become user-facing. |
| Terminators | Set `{"p", "q", "z", "h", "r"}` — any one ends a ticket | Cheat sheet + real fixture (`jersey_boys_q_terminator.fgl`) proves the doc's `<p>`-only assumption was too narrow. |
| Multi-ticket handling | Split on **any** terminator opcode, validate each segment, aggregate diagnostics | Doc recommended `<p>`-only; broaden to the full terminator set since real streams (`jersey_boys_ttf.fgl`) end on `<q>`. |
| Printer profiles | `PrinterProfile` dataclass passed to bounded rules; default `LEMUR` (2400×2400) | Doc warns hardcoding bounds is a future support ticket; cheap to do correctly now. |
| Test framework | `pytest` parametrized over fixture directory | Doc-prescribed; the corpus *is* the spec. |

## What We're NOT Doing

- Tree-sitter grammar / editor-side parsing.
- LSP server (pygls).
- Property-based tests (Hypothesis).
- A configuration file format for rule disables (`--config`). Add when there are real users.
- JSON output mode (`--format json`). Add when CI needs it.
- Pydantic, class hierarchies, or any rule framework beyond a decorator + list.
- Tightening `BARCODE_BODY` beyond the doc's regex — wait for corpus evidence first.
- Incremental reparsing.

## Implementation Approach

Build bottom-up: grammar → AST → rule plumbing → rule set + fixture corpus → CLI → multi-ticket / profile polish. Each phase ends with a runnable verification step. The fixture corpus arrives in Phase 3 and grows from then on; every later phase adds fixtures rather than ad-hoc tests.

## Executable Specifications (Outside-In)

No outside-in (BDD) harness — n/a. Phase 0 is omitted; the pytest fixture corpus introduced in Phase 3 plays the same role of accumulating executable behavior knowledge.

---

## Phase 1: Project scaffolding, grammar, smoke parse

### Overview

Stand up the Python project, write `fgl.lark`, instantiate the parser, and prove it can parse the Jersey Boys gist without exception.

### Changes Required

#### 1. `pyproject.toml`

```toml
[project]
name = "fgl-validator"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["lark>=1.1.9"]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
fgl-validate = "fgl_validator.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/fgl_validator"]
```

#### 2. `src/fgl_validator/__init__.py`

Empty (or re-export `validate` once it exists in Phase 3).

#### 3. `src/fgl_validator/fgl.lark`

Verbatim from `fgl-validator-lark.md:27-45`:

```lark
start: element*

element: command
       | barcode
       | TEXT
       | NEWLINE

command: "<" OPCODE args? ">"
args: INT ("," INT)*

barcode: ":" BARCODE_BODY ":"

OPCODE: /[A-Za-z]+/
INT: /[0-9]+/
BARCODE_BODY: /[^:\n<>]+/
TEXT: /[^<:\n]+/
NEWLINE: /\r?\n/
```

#### 4. `src/fgl_validator/parser.py`

```python
from pathlib import Path
from lark import Lark

GRAMMAR_PATH = Path(__file__).parent / "fgl.lark"
parser = Lark.open(str(GRAMMAR_PATH), parser="lalr", propagate_positions=True)
```

#### 5. `tests/fixtures/valid/` (already populated)

The corpus is already seeded from the BOCA gist (`gh api gists/dba5496db94082d22475953a3cd32a1c`):

- `cfg_dump.fgl` — config dump with `<VA#>` variables.
- `euro_chars.fgl` — non-ASCII bytes, two tickets in one stream.
- `jersey_boys_ttf.fgl` — full ticket, terminator `<q>`.
- `jersey_boys_rtf.fgl` — full ticket, terminator `<p>`.
- `jersey_boys_q_terminator.fgl` — alternate full ticket, terminator `<q>`.

Cached gist JSON lives at `.cache/gist.json` (gitignored).

#### 6. `tests/test_parser_smoke.py`

```python
from pathlib import Path
import pytest
from fgl_validator.parser import parser

VALID = Path(__file__).parent / "fixtures/valid"

@pytest.mark.parametrize("path", sorted(VALID.glob("*.fgl")))
def test_parses_without_exception(path):
    parser.parse(path.read_text())
```

### Success Criteria

#### Automated Verification

- [x] `uv sync --extra dev` resolves without error.
- [x] `uv run pytest tests/test_parser_smoke.py` passes.
- [x] `uv run python -c "from fgl_validator.parser import parser; parser.parse('<F3>HELLO<p>')"` exits 0.

#### Manual Verification

- [ ] Tree from `<F3>HELLO<p>` shows opcode `F` with arg `3` (not opcode `F3`).
- [ ] Whitespace inside `JERSEY BOYS` text is preserved (visible in tree dump).

---

## Phase 2: AST transformer + diagnostic/rule framework

### Overview

Add the `FGLTransformer` and the `Diagnostic` / `Rule` plumbing including the `validate()` runner. No rules yet — a registered no-op rule proves the wiring.

### Changes Required

#### 1. `src/fgl_validator/ast.py`

Dataclasses from `fgl-validator-lark.md:71-90`:

```python
from dataclasses import dataclass

@dataclass
class Command:
    opcode: str
    args: list[int]
    line: int
    col: int

@dataclass
class Barcode:
    body: str
    line: int
    col: int

@dataclass
class Text:
    value: str
    line: int
    col: int

Node = Command | Barcode | Text
```

#### 2. `src/fgl_validator/transformer.py`

Verbatim shape from `fgl-validator-lark.md:92-117`. Critical detail: `start()` flattens, dropping `NEWLINE` tokens and wrapping bare `TEXT` tokens.

#### 3. `src/fgl_validator/diagnostic.py`

```python
from dataclasses import dataclass
from typing import Callable, Iterable, Literal

Severity = Literal["error", "warning", "info"]

@dataclass
class Diagnostic:
    code: str
    severity: Severity
    message: str
    line: int
    col: int
```

#### 4. `src/fgl_validator/rules.py`

```python
from typing import Callable, Iterable
from .ast import Node
from .diagnostic import Diagnostic

Rule = Callable[[list[Node]], Iterable[Diagnostic]]

RULES: list[Rule] = []

def rule(fn: Rule) -> Rule:
    RULES.append(fn)
    return fn
```

#### 5. `src/fgl_validator/validate.py`

```python
from .parser import parser
from .transformer import FGLTransformer
from .diagnostic import Diagnostic
from .rules import RULES

def validate(source: str) -> list[Diagnostic]:
    try:
        tree = parser.parse(source)
    except Exception as e:
        return [Diagnostic("FGL000", "error", str(e),
                           getattr(e, "line", 1), getattr(e, "column", 1))]
    nodes = FGLTransformer().transform(tree)
    diags: list[Diagnostic] = []
    for r in RULES:
        diags.extend(r(nodes))
    diags.sort(key=lambda d: (d.line, d.col, d.code))
    return diags
```

#### 6. `src/fgl_validator/__init__.py`

Re-export: `from .validate import validate`.

#### 7. `tests/test_validate_wiring.py`

```python
from fgl_validator import validate

def test_returns_parse_error_for_garbage():
    diags = validate("<<<")
    assert any(d.code == "FGL000" for d in diags)

def test_clean_input_no_diagnostics_yet():
    assert validate("<F>3<p>") == []  # no rules registered yet
```

### Success Criteria

#### Automated Verification

- [x] `uv run pytest` passes.
- [x] `uv run python -c "from fgl_validator import validate; print(validate('<p>'))"` prints `[]`.

#### Manual Verification

- [ ] `validate("<<<")` returns one `FGL000` diagnostic with a sane line/col (not always `(1,1)` — the message should reflect the actual parse failure point).

---

## Phase 3: Initial rule set + fixture corpus

### Overview

Implement the six MVP rules and back each with at least one fixture in `tests/fixtures/{valid,invalid}/`. The parametrized harness becomes the project's executable spec.

### Changes Required

#### 1. `src/fgl_validator/rule_set.py`

Implement, in this order, importing `rule` from `.rules` so each is auto-registered:

- `FGL001 unknown_opcode` — `fgl-validator-lark.md:162-170`
- `FGL002 wrong_arity` — `fgl-validator-lark.md:172-182`
- `FGL003 coordinate_bounds` — `fgl-validator-lark.md:184-194`. Take `profile: PrinterProfile` parameter via closure (see Phase 5); for now hardcode `max_x=max_y=2400` and `# TODO(phase-5): pull from profile`.
- `FGL004 must_terminate` — broaden the doc's `must_terminate_with_print` (`fgl-validator-lark.md:196-207`) to accept any opcode in `TERMINATORS = {"p", "q", "z", "h", "r"}`. Message: `"Ticket must terminate with one of <p>/<q>/<z>/<h>/<r>"`.
- `FGL005 hw_paired` — `fgl-validator-lark.md:209-225`. Trigger emit on **any** terminator (not just `<p>`).

`KNOWN_OPCODES` is seeded from the BOCA cheat sheet (gist `readme.md`):

```python
KNOWN_OPCODES: dict[str, int] = {
    # Rotation
    "NR": 0, "RR": 0, "RU": 0, "RL": 0,
    # Layout / cursor
    "RC": 2, "SP": 2,
    # Fonts
    "F": 1, "TT": 1, "TTF": 2, "RTF": 2,
    "HW": 2, "SD": 1,
    # Lines / boxes
    "LT": 1, "BS": 2, "BX": 2, "VX": 1, "HX": 1,
    # Logos / graphics
    "LD": 1, "LO": 1, "G": 1, "g": 1,
    # Buffer / repeat
    "CB": 0, "RE": 1,
    # Inverse / transparent
    "EI": 0, "DI": 0, "t": 0, "n": 0,
    # Barcode setup
    "X": 1, "BI": 0, "AXB": 1, "FL": 1,
    # Ladder barcodes
    "Ul": 1, "EL": 1, "NL": 1, "CL": 1, "OL": 1,
    # Picket-fence barcodes
    "UP": 1, "EP": 1, "NP": 1, "FP": 1, "CP": 1, "OP": 1,
    # Output / control
    "PL": 1, "RO": 1, "ME": 0, "MD": 0, "TRE": 0,
    # Status
    "S": 1, "PC": 0, "TC": 1,
    # Variables
    "VA": 1,
    # Terminators (lowercase)
    "p": 0, "q": 0, "z": 0, "h": 0, "r": 0,
}

TERMINATORS = frozenset({"p", "q", "z", "h", "r"})
```

Cross-check during implementation: parse every `tests/fixtures/valid/*.fgl` and assert no `FGL001` (unknown_opcode) diagnostics fire. If any do, the cheat-sheet-derived map is wrong — fix it (don't suppress).

Ensure `rule_set` is imported at package init so registration happens (`src/fgl_validator/__init__.py` adds `from . import rule_set  # noqa: F401`).

#### 2. Fixture corpus

```
tests/fixtures/
  valid/
    cfg_dump.fgl                 # already in repo (gist CFG.html)
    euro_chars.fgl               # already in repo (gist Euro.html)
    jersey_boys_ttf.fgl          # already in repo (gist FGL1.html, terminator <q>)
    jersey_boys_rtf.fgl          # already in repo (gist FGL2.html, terminator <p>)
    jersey_boys_q_terminator.fgl # already in repo (gist FGL3.html, terminator <q>)
    minimal_p.fgl                # "<F3>HELLO<p>"
    minimal_q.fgl                # "<F3>HELLO<q>"      — proves FGL004 accepts <q>
    barcode_only.fgl             # ":12345:<p>"
  invalid/
    missing_terminator.fgl       # no terminating opcode at all
    missing_terminator.expected.json   # [{"code": "FGL004"}]
    bad_coords.fgl               # "<RC9999,9999><p>"
    bad_coords.expected.json
    unknown_opcode.fgl           # "<ZZ><p>"
    unknown_opcode.expected.json
    wrong_arity.fgl              # "<RC10><p>"   (RC needs 2 args, given 1)
    wrong_arity.expected.json
    hw_left_set.fgl              # "<HW3,3>FOO<p>"
    hw_left_set.expected.json
```

`*.expected.json` is a list of `{"code": "FGL00X", "line": N}` entries; only `(code, line)` pairs are compared per `fgl-validator-lark.md:289-291`.

#### 3. `tests/test_corpus.py`

Verbatim shape from `fgl-validator-lark.md:274-291`.

### Success Criteria

#### Automated Verification

- [x] `uv run pytest tests/test_corpus.py -v` — every fixture passes.
- [x] `uv run pytest` — full suite green.
- [x] Adding a new `valid/foo.fgl` containing only `<p>` passes without changes elsewhere.

#### Manual Verification

- [ ] Each rule has at least one `invalid/` fixture that exercises it.
- [ ] `validate(jersey_boys_text)` returns `[]`.
- [ ] Diagnostic ordering is stable (sorted by `(line, col, code)`).

---

## Phase 4: CLI

### Overview

Wire `python -m fgl_validator <path>` to print human-readable diagnostics and exit non-zero on errors.

### Changes Required

#### 1. `src/fgl_validator/__main__.py`

Per `fgl-validator-lark.md:309-322`:

```python
import sys
from pathlib import Path
from . import validate

def main():
    path = Path(sys.argv[1])
    diags = validate(path.read_text())
    for d in diags:
        print(f"{path}:{d.line}:{d.col}: {d.severity}: [{d.code}] {d.message}")
    sys.exit(1 if any(d.severity == "error" for d in diags) else 0)

if __name__ == "__main__":
    main()
```

#### 2. `tests/test_cli.py`

```python
import subprocess, sys
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"

def run(path):
    return subprocess.run(
        [sys.executable, "-m", "fgl_validator", str(path)],
        capture_output=True, text=True,
    )

def test_cli_valid_exits_zero():
    r = run(FIXTURES / "valid/jersey_boys.fgl")
    assert r.returncode == 0

def test_cli_missing_print_exits_one():
    r = run(FIXTURES / "invalid/missing_print.fgl")
    assert r.returncode == 1
    assert "[FGL004]" in r.stdout
```

### Success Criteria

#### Automated Verification

- [x] `uv run pytest tests/test_cli.py` passes.
- [x] `uv run python -m fgl_validator tests/fixtures/valid/jersey_boys_rtf.fgl; echo $?` prints `0`.
- [x] `uv run python -m fgl_validator tests/fixtures/invalid/missing_terminator.fgl; echo $?` prints `1`.

#### Manual Verification

- [ ] CLI output format matches `path:line:col: severity: [code] message`.

---

## Phase 5: Multi-ticket streams + printer profiles

### Overview

Address two doc-flagged real-world concerns: a single input may contain N tickets each ending in `<p>`, and coordinate bounds vary per printer.

### Changes Required

#### 1. `src/fgl_validator/profile.py`

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class PrinterProfile:
    name: str
    max_x: int
    max_y: int

LEMUR = PrinterProfile("Lemur", 2400, 2400)
LEMUR_K = PrinterProfile("Lemur-K", 2400, 1200)  # placeholder; verify against printer datasheet
FGL46 = PrinterProfile("FGL46", 4800, 4800)      # placeholder

PROFILES = {p.name.lower(): p for p in (LEMUR, LEMUR_K, FGL46)}
DEFAULT = LEMUR
```

(Real values pulled from BOCA datasheets during this phase; unknown values flagged as TODO and any not-yet-verified profile gated behind a comment until confirmed.)

#### 2. Refactor `validate()` to take `profile` and split on `<p>`

```python
def validate(source: str, profile: PrinterProfile = DEFAULT) -> list[Diagnostic]:
    # parse once, transform once, then segment node stream on <p> boundaries
    ...
```

Segmentation: walk the transformed `nodes`; each time a `Command` whose opcode is in `TERMINATORS` is seen, close the current segment (inclusive of the terminator) and start a new one. Run rules per segment, collect diagnostics, prepend nothing — line/col are already absolute from the transformer. Trailing nodes after the last terminator form a final segment that will (correctly) trip `FGL004`. Empty trailing whitespace-only segments (e.g. one trailing `\n`) are dropped.

`FGL003 coordinate_bounds` becomes a closure: `make_coordinate_bounds(profile)` returns the rule. Replace the `@rule` decorator usage for that rule with explicit `RULES.append(...)` at validate-time, **or** thread `profile` through a shared context object passed to every rule. Choose the closure approach — minimal change, no rule signature churn.

This means `RULES` becomes "rules that don't need profile" + a per-call list of profile-bound rules. Concretely:

```python
def validate(source, profile=DEFAULT):
    ...
    rules = RULES + [make_coordinate_bounds(profile)]
    for r in rules:
        ...
```

And remove `coordinate_bounds` from the auto-registered set.

#### 3. CLI flag

`--profile NAME` (default `lemur`), looked up in `PROFILES`. Unknown name → exit 2 with stderr message.

#### 4. Fixtures

Add:

```
tests/fixtures/valid/two_tickets.fgl    # "<F>3A<p><F>3B<p>"
tests/fixtures/invalid/two_tickets_second_missing_p.fgl
tests/fixtures/invalid/two_tickets_second_missing_p.expected.json
tests/fixtures/invalid/bad_coords_lemur.fgl   # 2401,2401 — fails on Lemur, would pass on FGL46
```

### Success Criteria

#### Automated Verification

- [x] `uv run pytest` green.
- [x] `uv run python -m fgl_validator --profile lemur tests/fixtures/invalid/bad_coords_lemur.fgl` exits 1 and prints `[FGL003]`.
- [x] `uv run python -m fgl_validator --profile fgl46 tests/fixtures/invalid/bad_coords_lemur.fgl` exits 0 (assuming `FGL46` bounds verified ≥2401).
- [x] Two-ticket fixture: a missing `<p>` on the second ticket emits one `FGL004`, not two.

#### Manual Verification

- [ ] BOCA datasheet values for `LEMUR_K` and `FGL46` are filled in (no `placeholder` comments left).
- [ ] Multi-ticket diagnostic line numbers correspond to the source (sanity-check with `cat -n`).

---

## Testing Strategy

### Unit / corpus tests

- Phase 1: parser smoke (one valid file).
- Phase 2: `validate()` wiring — parse error path and empty-rules path.
- Phase 3 onward: every behavior change is a fixture pair (`valid/*.fgl` or `invalid/{name}.fgl + name.expected.json`). The corpus is the spec.

### Manual testing

- After each phase, run the CLI on `tests/fixtures/valid/jersey_boys.fgl` and on at least one `invalid/` fixture.
- After Phase 5, smoke-test a real multi-ticket sample if available.

## Performance Considerations

The doc targets <50ms per typical ticket (`fgl-validator-lark.md:334`). Lark LALR + a flat node walk is comfortably within that. No optimization work planned. If a perf regression appears, profile before optimizing.

## Migration Notes

N/A — greenfield repo.

## References

- Source spec: `/Users/willclark/Downloads/fgl-validator-lark.md`
- Grammar: `fgl-validator-lark.md:25-45`
- AST shape: `fgl-validator-lark.md:67-117`
- Diagnostic shape: `fgl-validator-lark.md:130-138`
- Example rules: `fgl-validator-lark.md:152-225`
- Runner: `fgl-validator-lark.md:233-246`
- Fixture-corpus testing pattern: `fgl-validator-lark.md:274-291`
- CLI: `fgl-validator-lark.md:309-322`
- FGL gotchas (whitespace, opcode boundary, `<p>` casing, multi-ticket, profile bounds): `fgl-validator-lark.md:296-304`
