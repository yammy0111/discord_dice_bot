# dice/parser.py

from __future__ import annotations

from .nodes import (
    ASTNode,
    NumberNode,
    DiceNode,
    UnaryOpNode,
    BinaryOpNode,
    PercentNode,
)

from .tokenizer import (
    Token,
    TokenType,
)
from .errors import ParserError


class Parser:

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.index = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.index]

    def advance(self) -> None:
        if self.index < len(self.tokens) - 1:
            self.index += 1

    def consume(
        self,
        expected: TokenType,
    ) -> Token:

        token = self.current

        if token.type != expected:
            raise ParserError(
                f"예상: {expected.name}, 실제: {token.type.name}"
            )

        self.advance()
        return token

    def parse(self) -> ASTNode:
        node = self.expression()

        if self.current.type != TokenType.EOF:
            raise ParserError(
                "수식 끝에 불필요한 토큰이 있습니다."
            )

        return node

    # lowest precedence
    def expression(self) -> ASTNode:

        node = self.term()

        while self.current.type in (
            TokenType.PLUS,
            TokenType.MINUS,
        ):
            op = self.current.value
            self.advance()

            node = BinaryOpNode(
                left=node,
                operator=op,
                right=self.term(),
            )

        return node

    def term(self) -> ASTNode:

        node = self.power()

        while self.current.type in (
            TokenType.MUL,
            TokenType.DIV,
        ):
            op = self.current.value
            self.advance()

            node = BinaryOpNode(
                left=node,
                operator=op,
                right=self.power(),
            )

        return node

    def power(self) -> ASTNode:

        node = self.unary()

        if self.current.type == TokenType.POW:
            op = self.current.value

            self.advance()

            node = BinaryOpNode(
                left=node,
                operator=op,
                right=self.power(),
            )

        return node

    def unary(self) -> ASTNode:

        if self.current.type == TokenType.PLUS:
            self.advance()

            return UnaryOpNode(
                operator="+",
                operand=self.unary(),
            )

        if self.current.type == TokenType.MINUS:
            self.advance()

            return UnaryOpNode(
                operator="-",
                operand=self.unary(),
            )

        return self.primary()

    def primary(self) -> ASTNode:

        token = self.current

        # ( expression )
        if token.type == TokenType.LPAREN:
            self.advance()
            node = self.expression()
            self.consume(TokenType.RPAREN)

        elif token.type == TokenType.NUMBER:
            num_val: int | float = float(token.value) if "." in token.value else int(token.value)
            if isinstance(num_val, float) and num_val.is_integer():
                num_val = int(num_val)
            self.advance()

            # NdM or Nd%
            if self.current.type == TokenType.D:
                if isinstance(num_val, float):
                    raise ParserError("주사위 개수는 정수여야 합니다.")
                self.advance()

                if self.current.type == TokenType.PERCENT:
                    self.advance()
                    node = DiceNode(count=num_val, sides=100)
                else:
                    sides_token = self.consume(TokenType.NUMBER)
                    sides_val: int | float = float(sides_token.value) if "." in sides_token.value else int(sides_token.value)
                    if isinstance(sides_val, float) and not sides_val.is_integer():
                        raise ParserError("주사위 면 수는 정수여야 합니다.")
                    node = DiceNode(
                        count=num_val,
                        sides=int(sides_val),
                    )
            else:
                node = NumberNode(num_val)

        # d20 or d%
        elif token.type == TokenType.D:
            self.advance()

            if self.current.type == TokenType.PERCENT:
                self.advance()
                node = DiceNode(count=1, sides=100)
            else:
                sides_token = self.consume(TokenType.NUMBER)
                sides_val = float(sides_token.value) if "." in sides_token.value else int(sides_token.value)
                if isinstance(sides_val, float) and not sides_val.is_integer():
                    raise ParserError("주사위 면 수는 정수여야 합니다.")
                node = DiceNode(
                    count=1,
                    sides=int(sides_val),
                )
        else:
            raise ParserError(
                f"예상치 못한 토큰: {token.type.name}"
            )

        # 후위 % (백분율) 연산자 처리
        while self.current.type == TokenType.PERCENT:
            self.advance()
            node = PercentNode(operand=node)

        

        return node