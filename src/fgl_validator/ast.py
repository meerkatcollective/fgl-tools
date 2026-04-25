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
