from .ast import Command
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
