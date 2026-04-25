from typing import Callable, Iterable

from .ast import Node
from .diagnostic import Diagnostic

Rule = Callable[[list[Node]], Iterable[Diagnostic]]

RULES: list[Rule] = []


def rule(fn: Rule) -> Rule:
    RULES.append(fn)
    return fn
