from lark import Transformer, Token, v_args

from .ast import Command, Barcode, Text


class FGLTransformer(Transformer):
    @v_args(meta=True)
    def command(self, meta, items):
        opcode = str(items[0])
        args = items[1] if len(items) > 1 else []
        return Command(opcode, args, meta.line, meta.column)

    @v_args(meta=True)
    def barcode(self, meta, items):
        # Grammar: barcode: BARCODE  where BARCODE = /:[^:\n<>\s]+:/
        # Strip the leading and trailing colons to get the body.
        raw = str(items[0])
        body = raw[1:-1]
        return Barcode(body, meta.line, meta.column)

    def args(self, items):
        return [int(t) for t in items]

    def element(self, items):
        # items is a list with one entry: Command, Barcode, TEXT token, or NEWLINE token
        item = items[0]
        if isinstance(item, Token):
            if item.type == "TEXT":
                return Text(str(item), item.line, item.column)
            # NEWLINE: discard
            return None
        return item  # Command or Barcode

    def start(self, items):
        return [it for it in items if it is not None]
