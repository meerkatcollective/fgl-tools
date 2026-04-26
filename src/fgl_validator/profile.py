from dataclasses import dataclass


@dataclass(frozen=True)
class PrinterProfile:
    name: str
    max_x: int
    max_y: int
    max_ink_mass: int  # Ladder-barcode ink-mass cap; see references/ink-budget.md.


# Lemur ink budget is empirical: cliff between OL*X^2 = 80 and 96 for a 16-char Code 128
# ladder => ~45k mass. Set the cap just below the cliff so warnings fire before hardware drops content.
LEMUR = PrinterProfile("Lemur", 2400, 2400, max_ink_mass=45000)
LEMUR_K = PrinterProfile("Lemur-K", 2400, 1200, max_ink_mass=45000)  # ink budget unverified — same as Lemur until measured
FGL46 = PrinterProfile("FGL46", 4800, 4800, max_ink_mass=90000)      # ink budget unverified — placeholder doubled for larger printer

PROFILES = {p.name.lower(): p for p in (LEMUR, LEMUR_K, FGL46)}
DEFAULT = LEMUR
