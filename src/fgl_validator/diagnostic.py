from dataclasses import dataclass
from typing import Literal

Severity = Literal["error", "warning", "info"]


@dataclass
class Diagnostic:
    code: str
    severity: Severity
    message: str
    line: int
    col: int
