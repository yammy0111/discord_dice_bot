# dice/tokenizer.py

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    NUMBER = auto()

    D = auto()  # d

    PLUS = auto()
    MINUS = auto()

    MUL = auto()
    DIV = auto()
    PERCENT = auto()  # %

    POW = auto()

    LPAREN = auto()
    RPAREN = auto()

    EOF = auto()


@dataclass(slots=True)
class Token:
    type: TokenType
    value: str
    position: int

    def __repr__(self) -> str:
        return (
            f"Token("
            f"type={self.type.name}, "
            f"value={self.value!r}, "
            f"pos={self.position}"
            f")"
        )


from .errors import TokenizerError


class Tokenizer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.length = len(text)

    def current_char(self) -> str | None:
        if self.pos >= self.length:
            return None
        return self.text[self.pos]

    def advance(self) -> None:
        self.pos += 1

    def skip_whitespace(self) -> None:
        while True:
            ch = self.current_char()

            if ch is None or not ch.isspace():
                break

            self.advance()

    def read_number(self) -> Token:
        start = self.pos

        while True:
            ch = self.current_char()

            if ch is None or not ch.isdigit():
                break

            self.advance()

        return Token(
            TokenType.NUMBER,
            self.text[start:self.pos],
            start,
        )

    def next_token(self) -> Token:
        self.skip_whitespace()

        ch = self.current_char()

        if ch is None:
            return Token(
                TokenType.EOF,
                "",
                self.pos,
            )

        if ch.isdigit():
            return self.read_number()

        start = self.pos

        if ch in ("d", "D"):
            self.advance()
            return Token(TokenType.D, "d", start)

        if ch == "+":
            self.advance()
            return Token(TokenType.PLUS, "+", start)

        if ch == "-":
            self.advance()
            return Token(TokenType.MINUS, "-", start)

        if ch == "*":
            self.advance()

            if self.current_char() == "*":
                self.advance()
                return Token(TokenType.POW, "**", start)

            return Token(TokenType.MUL, "*", start)

        if ch == "/":
            self.advance()
            return Token(TokenType.DIV, "/", start)

        if ch == "%":
            self.advance()
            return Token(TokenType.PERCENT, "%", start)

        if ch == "(":
            self.advance()
            return Token(TokenType.LPAREN, "(", start)

        if ch == ")":
            self.advance()
            return Token(TokenType.RPAREN, ")", start)

        raise TokenizerError(
            f"허용되지 않는 문자 '{ch}' (위치: {start})"
        )

    def tokenize(self) -> list[Token]:
        result = list[Token]()
        while True:
            token = self.next_token()

            result.append(token)

            if token.type == TokenType.EOF:
                break

        return result
