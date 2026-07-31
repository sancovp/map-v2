"""Small Prolog statement splitter used by MAP's authored-fact boundary."""

from __future__ import annotations


def split_statements(text: str, source: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False
    in_comment = False
    start_line = 1
    line_number = 1
    for char in text:
        if in_comment:
            if char == "\n":
                in_comment = False
                line_number += 1
            continue
        if quote:
            current.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            if char == "\n":
                line_number += 1
            continue
        if char == "%":
            in_comment = True
            continue
        if char in {"'", '"'}:
            quote = char
            current.append(char)
            continue
        if char == ".":
            current.append(char)
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            start_line = line_number
            continue
        current.append(char)
        if char == "\n":
            line_number += 1
    trailing = "".join(current).strip()
    if trailing:
        raise ValueError(
            f"Unterminated statement in {source} starting at line {start_line}"
        )
    return statements
