from pathlib import Path
from lark import Lark

GRAMMAR_PATH = Path(__file__).parent / "fgl.lark"
parser = Lark.open(str(GRAMMAR_PATH), parser="lalr", propagate_positions=True)
