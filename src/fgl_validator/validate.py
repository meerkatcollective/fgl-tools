from .parser import parser
from .transformer import FGLTransformer
from .ast import Command, Text, Barcode
from .diagnostic import Diagnostic
from .rules import RULES
from .profile import PrinterProfile, DEFAULT
from .rule_set import TERMINATORS, make_coordinate_bounds, make_barcode_ink_mass


def _segment_nodes(nodes):
    """Split a flat node list into per-ticket segments.

    Each time a Command whose opcode is in TERMINATORS is encountered, the
    current segment (inclusive of the terminator) is closed and a new one
    starts.  Any trailing nodes after the last terminator form a final segment
    (which will correctly trip FGL004 if non-empty non-whitespace content is
    present).  Trailing segments that contain only whitespace Text nodes are
    dropped silently.
    """
    segments = []
    current: list = []
    for node in nodes:
        current.append(node)
        if isinstance(node, Command) and node.opcode in TERMINATORS:
            segments.append(current)
            current = []
    # Trailing segment — only include if it has non-whitespace content
    if current:
        has_content = any(
            isinstance(n, Command) or isinstance(n, Barcode) or
            (isinstance(n, Text) and n.value.strip())
            for n in current
        )
        if has_content:
            segments.append(current)
    return segments


def validate(source: str, profile: PrinterProfile = DEFAULT) -> list[Diagnostic]:
    try:
        tree = parser.parse(source)
    except Exception as e:
        return [Diagnostic("FGL000", "error", str(e),
                           getattr(e, "line", 1), getattr(e, "column", 1))]

    nodes = FGLTransformer().transform(tree)

    # Build rule list: profile-independent rules + profile-bound FGL003 / FGL006
    rules = RULES + [make_coordinate_bounds(profile), make_barcode_ink_mass(profile)]

    # Segment the node stream on terminator boundaries
    segments = _segment_nodes(nodes)

    # If the file is entirely empty/whitespace, treat as single empty segment
    if not segments:
        segments = [nodes]

    diags: list[Diagnostic] = []
    for segment in segments:
        for r in rules:
            diags.extend(r(segment))

    diags.sort(key=lambda d: (d.line, d.col, d.code))
    return diags
