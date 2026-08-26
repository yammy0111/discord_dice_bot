# dice/engine.py

from __future__ import annotations

from dataclasses import dataclass

from .tokenizer import Tokenizer
from .parser import Parser
from .evaluator import Evaluator
from .renderer import Renderer
from .limits import MAX_EXPRESSIONS_COUNT
from .errors import DiceError, LimitExceededError
from .models import (
    EngineResult,
    RollEntry,
    RenderResult,
)


class DiceEngine:

    def __init__(self):
        self.renderer = Renderer()

    def roll(
        self,
        expression: str,
    ) -> EngineResult:

        expression = expression.strip()

        if not expression:
            raise DiceError("비어있는 수식입니다.")

        # 1. Tokenize
        tokenizer = Tokenizer(expression)
        tokens = tokenizer.tokenize()

        # 2. Parse
        parser = Parser(tokens)
        ast_tree = parser.parse()

        # 3. Evaluate
        evaluator = Evaluator()
        (
            value,
            substituted_expression,
            roll_logs,
        ) = evaluator.evaluate(ast_tree)

        # 4. Render
        render_result = self.renderer.render(
            expression_tree=ast_tree,
            substituted=substituted_expression,
            final_result=value,
        )

        return EngineResult(
            expression=expression,
            value=value,
            substituted_expression=substituted_expression,
            calculation_steps=render_result.steps,
            roll_logs=roll_logs,
            render_result=render_result,
        )

    def roll_multiple(
        self,
        raw_expression: str,
    ) -> list[EngineResult]:
        """
        쉼표(,)로 구분된 여러 주사위 표현식을 순차적으로 평가
        """
        parts = [p.strip() for p in raw_expression.split(",") if p.strip()]

        if not parts:
            raise DiceError("유효한 주사위 수식이 없습니다.")

        if len(parts) > MAX_EXPRESSIONS_COUNT:
            raise LimitExceededError(
                f"한 번에 굴릴 수 있는 수식 제한 ({MAX_EXPRESSIONS_COUNT}개 초과)"
            )

        results = []
        for part in parts:
            results.append(self.roll(part))

        return results