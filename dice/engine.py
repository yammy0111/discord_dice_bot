# dice/engine.py

from __future__ import annotations

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
    DerivedResult,
    DerivedRollResult,
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

    def roll_derived(
        self,
        raw_expression: str,
    ) -> DerivedRollResult:
        """
        '>' 구문으로 기본 주사위 굴림과 파생 계산식을 처리

        예: '2d6 > +5, *2+3'
          - 기본 굴림: 2d6 = 8
          - 파생 1: 8+5 = 13
          - 파생 2: 8*2+3 = 19
        """
        if ">" not in raw_expression:
            raise DiceError("파생 계산에는 '>' 구분자가 필요합니다. 예: 2d6 > +5, *2+3")

        parts = raw_expression.split(">", 1)
        base_expr = parts[0].strip()
        formulas_str = parts[1].strip()

        if not base_expr:
            raise DiceError("기본 주사위 수식이 비어있습니다.")

        if not formulas_str:
            raise DiceError("파생 계산식이 비어있습니다.")

        # 기본 주사위 굴림
        base_result = self.roll(base_expr)
        base_value = base_result.value

        # 파생 계산식 처리
        formulas = [f.strip() for f in formulas_str.split(",") if f.strip()]

        if not formulas:
            raise DiceError("유효한 파생 계산식이 없습니다.")

        if len(formulas) > MAX_EXPRESSIONS_COUNT:
            raise LimitExceededError(
                f"파생 계산식 제한 ({MAX_EXPRESSIONS_COUNT}개 초과)"
            )

        derived_results = []
        for formula in formulas:
            # 기본 값을 수식 앞에 붙여 완전한 수식을 만듦
            # 예: base=8, formula="+5" → "8+5"
            # 예: base=8, formula="*2+3" → "8*2+3"
            full_expr = f"{base_value}{formula}"
            try:
                result = self.roll(full_expr)
                derived_results.append(
                    DerivedResult(
                        formula=formula,
                        full_expression=full_expr,
                        value=result.value,
                        substituted_expression=result.substituted_expression,
                        calculation_steps=result.calculation_steps,
                    )
                )
            except DiceError as e:
                raise DiceError(
                    f"파생 계산식 '{formula}' 오류: {e}"
                )

        return DerivedRollResult(
            base=base_result,
            derived=derived_results,
        )