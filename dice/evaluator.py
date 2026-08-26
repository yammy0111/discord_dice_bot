# dice/evaluator.py

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List

from .nodes import (
    ASTNode,
    NumberNode,
    DiceNode,
    UnaryOpNode,
    BinaryOpNode,
    PercentNode,
)

from .limits import (
    MAX_DICE_COUNT,
    MAX_DICE_SIDES,
    MAX_TOTAL_ROLLS,
    MAX_POWER,
    MAX_RESULT_ABS,
)

from .errors import (
    EvaluatorError,
    LimitExceededError,
)


def _op_rank(op: str | None) -> int:
    if op in ("+", "-"):
        return 1
    if op in ("*", "/", "%"):
        return 2
    if op == "**":
        return 3
    return 99


def format_op(
    left_str: str,
    left_op: str | None,
    op: str,
    right_str: str,
    right_op: str | None,
) -> str:
    """연산자 우선순위에 맞춰 필요한 경우에만 괄호를 추가하는 헬퍼 함수"""
    parent_rank = _op_rank(op)

    # 피연산자 왼쪽
    if left_op and _op_rank(left_op) < parent_rank:
        left_str = f"({left_str})"

    # 피연산자 오른쪽
    if right_op:
        right_rank = _op_rank(right_op)
        if right_rank < parent_rank:
            right_str = f"({right_str})"
        elif parent_rank == 1 and op == "-" and right_op in ("+", "-"):
            right_str = f"({right_str})"
        elif parent_rank == 2 and op == "/" and right_op in ("*", "/"):
            right_str = f"({right_str})"
        elif op == "**":
            right_str = f"({right_str})"

    return f"{left_str}{op}{right_str}"


from .models import (
    RollEntry,
    EvalResult,
    EvaluationContext,
)


class Evaluator:

    def __init__(self):
        self.context = EvaluationContext([])

    # -----------------
    # Public API
    # -----------------

    def evaluate(
        self,
        node: ASTNode,
    ) -> tuple[
        int | float,
        str,
        list[RollEntry]
    ]:

        result = self._eval(node)

        value = result.value

        if isinstance(value, float):
            value = round(value, 2)

        return (
            value,
            result.rendered,
            self.context.roll_entries,
        )

    # -----------------
    # AST Evaluation
    # -----------------

    def _eval(
        self,
        node: ASTNode,
    ) -> EvalResult:

        if isinstance(node, NumberNode):
            return EvalResult(
                value=node.value,
                rendered=str(node.value),
                op_type=None,
            )

        if isinstance(node, DiceNode):
            return self._eval_dice(node)

        if isinstance(node, UnaryOpNode):
            return self._eval_unary(node)

        if isinstance(node, BinaryOpNode):
            return self._eval_binary(node)

        if isinstance(node, PercentNode):
            return self._eval_percent(node)

        raise EvaluatorError(
            f"지원하지 않는 노드 타입: {type(node).__name__}"
        )

    def _eval_percent(
        self,
        node: PercentNode,
    ) -> EvalResult:
        operand = self._eval(node.operand)
        val = operand.value / 100
        val = round(val, 4) if isinstance(val, float) else val
        return EvalResult(
            value=val,
            rendered=f"{operand.rendered}%",
            op_type="%",
        )

    # -----------------
    # Dice
    # -----------------

    def _eval_dice(
        self,
        node: DiceNode,
    ) -> EvalResult:

        count = node.count
        sides = node.sides

        if count <= 0:
            raise EvaluatorError("주사위 개수는 1 이상이어야 합니다.")
        if sides <= 0:
            raise EvaluatorError("주사위 면 수는 1 이상이어야 합니다.")

        if count > MAX_DICE_COUNT:
            raise LimitExceededError(
                f"주사위 개수 제한 ({MAX_DICE_COUNT}개 초과)"
            )

        if sides > MAX_DICE_SIDES:
            raise LimitExceededError(
                f"주사위 면 수 제한 ({MAX_DICE_SIDES}면 초과)"
            )

        self.context.total_roll_count += count

        if self.context.total_roll_count > MAX_TOTAL_ROLLS:
            raise LimitExceededError(
                f"총 주사위 굴림 수 제한 ({MAX_TOTAL_ROLLS}개 초과)"
            )

        rolls = [
            random.randint(1, sides)
            for _ in range(count)
        ]

        total = sum(rolls)

        self.context.roll_entries.append(
            RollEntry(
                expression=f"{count}d{sides}",
                rolls=rolls,
                total=total,
            )
        )

        if count == 1:
            rendered = str(rolls[0])
            op_type = None
        else:
            rendered = "+".join(map(str, rolls))
            op_type = "+"

        return EvalResult(
            value=total,
            rendered=rendered,
            op_type=op_type,
        )

    # -----------------
    # Unary
    # -----------------

    def _eval_unary(
        self,
        node: UnaryOpNode,
    ) -> EvalResult:

        operand = self._eval(node.operand)

        if node.operator == "+":
            return EvalResult(
                operand.value,
                f"+{operand.rendered}",
                op_type=None,
            )

        if node.operator == "-":
            return EvalResult(
                -operand.value,
                f"-{operand.rendered}",
                op_type=None,
            )

        raise EvaluatorError(
            f"지원하지 않는 단항 연산자: {node.operator}"
        )

    # -----------------
    # Binary
    # -----------------

    def _eval_binary(
        self,
        node: BinaryOpNode,
    ) -> EvalResult:

        left = self._eval(node.left)
        right = self._eval(node.right)

        op = node.operator

        if op == "+":
            value = left.value + right.value

        elif op == "-":
            value = left.value - right.value

        elif op == "*":
            value = left.value * right.value

        elif op == "/":
            if right.value == 0:
                raise EvaluatorError("0으로 나눌 수 없습니다.")
            value = left.value / right.value

        elif op == "%":
            if right.value == 0:
                raise EvaluatorError("0으로 나눌 수 없습니다.")
            value = left.value % right.value

        elif op == "**":
            if abs(right.value) > MAX_POWER:
                raise LimitExceededError(
                    f"거듭제곱 제한 ({MAX_POWER} 초과)"
                )
            try:
                value = left.value ** right.value
            except OverflowError:
                raise LimitExceededError(
                    f"계산 결과가 수치 범위를 초과했습니다."
                )
        else:
            raise EvaluatorError(
                f"지원하지 않는 연산자: {op}"
            )

        if isinstance(value, float):
            value = round(value, 2)

        if abs(value) > MAX_RESULT_ABS:
            raise LimitExceededError(
                f"계산 결과 한도 초과 (최대 {MAX_RESULT_ABS})"
            )

        rendered = format_op(
            left.rendered,
            left.op_type,
            op,
            right.rendered,
            right.op_type,
        )

        return EvalResult(
            value=value,
            rendered=rendered,
            op_type=op,
        )