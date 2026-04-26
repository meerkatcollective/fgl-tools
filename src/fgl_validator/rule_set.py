from .ast import Barcode, Command, Text
from .diagnostic import Diagnostic
from .rules import rule

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
    # Logos / graphics / files
    "LD": 1, "LO": 1, "G": 1, "g": 1,
    "DF": 1, "SF": 1, "ID": 1,
    # Buffer / repeat
    "CB": 0, "RE": 1,
    # Inverse / transparent
    "EI": 0, "DI": 0, "t": 0, "n": 0,
    # Barcode setup
    "X": 1, "BI": 0, "AXB": 1,
    # Ladder barcodes (uppercase = legacy, ignores rotation)
    "UL": 1, "EL": 1, "NL": 1, "CL": 1, "OL": 1, "FL": 1,
    # Ladder barcodes (lowercase = rotation-aware, preferred)
    "uL": 1, "eL": 1, "nL": 1, "cL": 1, "oL": 1, "fL": 1,
    # Picket-fence barcodes (uppercase + lowercase)
    "UP": 1, "EP": 1, "NP": 1, "FP": 1, "CP": 1, "OP": 1,
    "uP": 1, "eP": 1, "nP": 1, "fP": 1, "cP": 1, "oP": 1,
    # Output / control
    "PL": 1, "RO": 1, "ME": 0, "MD": 0, "TRE": 0,
    # Status
    "S": 1, "PC": 0, "TC": 1,
    # Variables
    "VA": 1,
    # Flash-write commands (must be sent standalone — see references/orientation.md)
    "rte": 0, "rtd": 0,
    "pl": 1, "tl": 1, "dpl": 0,
    "pf": 0, "tf": 0,
    "sb": 0, "mb": 0, "xe": 0, "cs": 0,
    # Terminators (lowercase)
    "p": 0, "q": 0, "z": 0, "h": 0, "r": 0,
}

TERMINATORS = frozenset({"p", "q", "z", "h", "r"})


@rule
def unknown_opcode(nodes):
    for n in nodes:
        if isinstance(n, Command) and n.opcode not in KNOWN_OPCODES:
            yield Diagnostic(
                "FGL001", "error",
                f"Unknown opcode <{n.opcode}>",
                n.line, n.col,
            )


@rule
def wrong_arity(nodes):
    for n in nodes:
        if isinstance(n, Command) and n.opcode in KNOWN_OPCODES:
            expected = KNOWN_OPCODES[n.opcode]
            if len(n.args) != expected:
                yield Diagnostic(
                    "FGL002", "error",
                    f"<{n.opcode}> expects {expected} args, got {len(n.args)}",
                    n.line, n.col,
                )


def make_coordinate_bounds(profile):
    """Return an FGL003 rule bound to the given PrinterProfile."""
    def coordinate_bounds(nodes):
        for n in nodes:
            if isinstance(n, Command) and n.opcode == "RC" and len(n.args) == 2:
                y, x = n.args
                if not (0 <= y <= profile.max_y and 0 <= x <= profile.max_x):
                    yield Diagnostic(
                        "FGL003", "error",
                        f"RC coordinate ({y},{x}) out of printer bounds",
                        n.line, n.col,
                    )
    return coordinate_bounds


@rule
def must_terminate(nodes):
    cmds = [n for n in nodes if isinstance(n, Command)]
    if not cmds or cmds[-1].opcode not in TERMINATORS:
        last = nodes[-1] if nodes else None
        line = last.line if last else 1
        col = last.col if last else 1
        yield Diagnostic(
            "FGL004", "error",
            "Ticket must terminate with one of <p>/<q>/<z>/<h>/<r>",
            line, col,
        )


# Ladder-barcode select opcodes mapped to (symbology_label, num_bars(N)).
# num_bars approximations come from the symbology spec; see references/ink-budget.md.
# Values for ladder symbologies only — picket-fence (P-suffix) is unmodelled.
# num_bars(N) approximations per symbology, calibrated against empirical mass
# measurements where available.  See references/ink-budget.md for derivation.
LADDER_SYMBOLOGIES: dict[str, tuple[str, callable]] = {
    # Code 128 calibrated from the TKTS booth iteration: 16-char data + X4 OL5
    # measured at ~43k mass, which back-solves to num_bars = 67 = 4*N + 3.
    "OL": ("Code 128", lambda n: 4 * n + 3),
    "oL": ("Code 128", lambda n: 4 * n + 3),
    # Code 39 spec: 9 modules/char, ~5 bars; start+stop add ~10 bars total.
    "NL": ("Code 39", lambda n: 5 * n + 10),
    "nL": ("Code 39", lambda n: 5 * n + 10),
    # I2of5: 5-module pairs, ~2 bars per digit.
    "FL": ("Interleaved 2 of 5", lambda n: 2 * n + 4),
    "fL": ("Interleaved 2 of 5", lambda n: 2 * n + 4),
    # Codabar: ~5 bars/char, start/stop ~6.
    "CL": ("Codabar", lambda n: 5 * n + 6),
    "cL": ("Codabar", lambda n: 5 * n + 6),
    # Fixed-length symbologies — bar count doesn't scale with input length.
    "UL": ("UPC-A", lambda n: 30),
    "uL": ("UPC-A", lambda n: 30),
    "EL": ("EAN-13", lambda n: 30),
    "eL": ("EAN-13", lambda n: 30),
}


def _strip_delimiters(s: str) -> str:
    """Strip a single matched delimiter pair from the head/tail of a barcode payload.

    Code 128 = ^DATA^, Code 39 = *DATA*, I2of5 (already a Barcode node) = :DATA:.
    """
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("^", "*"):
        return s[1:-1]
    return s


def make_barcode_ink_mass(profile):
    """Return an FGL006 rule bound to the given PrinterProfile.

    Walks the flat node list looking for the canonical barcode triplet
        <X#>  <ladder-select #>  <data>
    and warns when the computed ink mass exceeds profile.max_ink_mass.

    Mass formula for ladder symbologies (bars run along the long axis):
        mass = num_bars * bar_height_units * 8 * X^2
    where bar_height_units is the integer arg to the select command (e.g. OL5 -> 5).

    Picket-fence symbologies are deliberately not validated here — their X scaling is
    linear (not quadratic) and we don't have hardware-confirmed thresholds for them.
    """
    def barcode_ink_mass(nodes):
        cap = profile.max_ink_mass
        x_value = 1  # default <X1> if author never sets one
        i = 0
        while i < len(nodes):
            n = nodes[i]
            if isinstance(n, Command):
                if n.opcode == "X" and len(n.args) == 1:
                    x_value = n.args[0]
                elif n.opcode in LADDER_SYMBOLOGIES and len(n.args) == 1:
                    sym_name, bars_for = LADDER_SYMBOLOGIES[n.opcode]
                    bar_height_units = n.args[0]
                    # Find the next data-bearing node (Barcode or Text) — skip whitespace-only Text.
                    data_len = 0
                    for j in range(i + 1, len(nodes)):
                        m = nodes[j]
                        if isinstance(m, Barcode):
                            data_len = len(m.body)
                            break
                        if isinstance(m, Text):
                            stripped = _strip_delimiters(m.value)
                            if stripped.strip():
                                data_len = len(stripped)
                                break
                        if isinstance(m, Command):
                            break  # ran out of data context
                    if data_len > 0:
                        num_bars = bars_for(data_len)
                        mass = num_bars * bar_height_units * 8 * (x_value ** 2)
                        if mass > cap:
                            yield Diagnostic(
                                "FGL006", "warning",
                                f"{sym_name} barcode ink mass {mass} exceeds {profile.name} budget {cap} "
                                f"(bars={num_bars}, OL={bar_height_units}, X={x_value}); "
                                f"shrink X or OL, or split into a longer/shorter data string",
                                n.line, n.col,
                            )
            i += 1
    return barcode_ink_mass


@rule
def hw_paired(nodes):
    """<HW> changes are global state — flag a non-default HW left active at a terminator.

    Only fires if HW was explicitly reset to default at least once during the ticket,
    then changed away from default without a final reset.  This avoids false positives
    for tickets that set a non-default HW once at the start as a global layout setting.
    """
    _DEFAULT = (6, 6)
    current = _DEFAULT
    last_change = None
    had_explicit_reset = False

    for n in nodes:
        if isinstance(n, Command):
            if n.opcode == "HW" and len(n.args) == 2:
                current = tuple(n.args)
                last_change = n
                if current == _DEFAULT:
                    had_explicit_reset = True
            elif n.opcode in TERMINATORS:
                if current != _DEFAULT and had_explicit_reset and last_change:
                    yield Diagnostic(
                        "FGL005", "warning",
                        f"HW left at {current} at end of ticket; reset to {_DEFAULT}",
                        last_change.line, last_change.col,
                    )
