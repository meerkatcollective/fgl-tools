from dataclasses import dataclass


@dataclass(frozen=True)
class PrinterProfile:
    name: str
    max_x: int
    max_y: int


LEMUR = PrinterProfile("Lemur", 2400, 2400)
LEMUR_K = PrinterProfile("Lemur-K", 2400, 1200)  # unverified — update from BOCA datasheet
FGL46 = PrinterProfile("FGL46", 4800, 4800)       # unverified — update from BOCA datasheet

PROFILES = {p.name.lower(): p for p in (LEMUR, LEMUR_K, FGL46)}
DEFAULT = LEMUR
