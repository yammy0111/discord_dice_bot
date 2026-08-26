# dice/renderer.py

from __future__ import annotations

from dataclasses import dataclass

from .nodes import (
    ASTNode,
    NumberNode,
    DiceNode,
    UnaryOpNode,
    BinaryOpNode,
)
from .tokenizer import Tokenizer
from .parser import Parser
from .evaluator import format_op


@dataclass(slots=True)
class RenderResult:
    substituted: str
    steps: list[str]
    result: str


class Renderer:

    def render(
        self,
        expression_tree: ASTNode,
        substituted: str,
        final_result: int | float,
    ) -> RenderResult:

        steps: list[str] = []

        # substituted 수식을 다시 파싱하여 DiceNode가 없는 구문 트리 생성
        try:
            tokens = Tokenizer(substituted).tokenize()
            current: ASTNode = Parser(tokens).parse()
        except Exception:
            current = expression_tree

        max_steps = 50
        step_count = 0

        while not isinstance(current, NumberNode) and step_count < max_steps:
            reduced, changed = self._find_and_reduce(current)
            if not changed:
                break

            current = reduced
            step_str = self._to_string(current)

            # 불필요한 바깥 괄호 정리
            if step_str.startswith("(") and step_str.endswith(")"):
                inner = step_str[1:-1]
                if inner.count("(") == inner.count(")"):
                    step_str = inner

            if step_str not in steps and step_str != substituted and step_str != str(final_result):
                steps.append(step_str)

            step_count += 1

        return RenderResult(
            substituted=substituted,
            steps=steps,
            result=str(final_result),
        )

    # --------------------
    # 가장 안쪽 연산 계산
    # --------------------

    def _find_and_reduce(
        self,
        node: ASTNode,
    ) -> tuple[ASTNode, bool]:

        if isinstance(node, NumberNode):
            return node, False

        if isinstance(node, UnaryOpNode):
            if isinstance(node.operand, NumberNode):
                value = node.operand.value
                if node.operator == "-":
                    value = -value
                return NumberNode(value), True

            new_operand, changed = self._find_and_reduce(node.operand)
            return UnaryOpNode(node.operator, new_operand), changed

        if isinstance(node, BinaryOpNode):
            if isinstance(node.left, NumberNode) and isinstance(node.right, NumberNode):
                return (
                    NumberNode(
                        self._calc(
                            node.left.value,
                            node.operator,
                            node.right.value,
                        )
                    ),
                    True,
                )

            left, changed = self._find_and_reduce(node.left)
            if changed:
                return (
                    BinaryOpNode(
                        left,
                        node.operator,
                        node.right,
                    ),
                    True,
                )

            right, changed = self._find_and_reduce(node.right)
            return (
                BinaryOpNode(
                    node.left,
                    node.operator,
                    right,
                ),
                changed,
            )

        return node, False

    # --------------------
    # 실제 계산
    # --------------------

    def _calc(
        self,
        left: int | float,
        op: str,
        right: int | float,
    ) -> int | float:

        if op == "+":
            return left + right

        if op == "-":
            return left - right

        if op == "*":
            return left * right

        if op == "/":
            if right == 0:
                return 0
            val = left / right
            return round(val, 2) if isinstance(val, float) else val

        if op == "**":
            return left ** right

        raise ValueError(f"알 수 없는 연산자 {op}")

    # --------------------
    # AST → 문자열
    # --------------------

    def _to_string(
        self,
        node: ASTNode,
    ) -> str:

        if isinstance(node, NumberNode):
            return str(node.value)

        if isinstance(node, UnaryOpNode):
            return node.operator + self._to_string(node.operand)

        if isinstance(node, BinaryOpNode):
            left_str = self._to_string(node.left)
            left_op = node.left.operator if isinstance(node.left, BinaryOpNode) else None
            right_str = self._to_string(node.right)
            right_op = node.right.operator if isinstance(node.right, BinaryOpNode) else None
            return format_op(left_str, left_op, node.operator, right_str, right_op)

        return str(node)