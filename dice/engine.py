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
        '>' 구문으로 기본 주사위 굴림과 단계별 파생 계산식을 처리

        예: '2d6 > +5, *2+3 > -1'
          - 기본 굴림: 2d6 = 8
          - 1차 파생: 8+5 = 13, 8*2+3 = 19
          - 2차 파생: 13-1 = 12, 19-1 = 18
        """
        if ">" not in raw_expression:
            raise DiceError("파생 계산에는 '>' 구분자가 필요합니다. 예: 2d6 > +5, *2+3")

        sections = [section.strip() for section in raw_expression.split(">")]
        base_expr = sections[0]
        derived_sections = sections[1:]

        if not base_expr:
            raise DiceError("기본 주사위 수식이 비어있습니다.")

        if not derived_sections or any(not section for section in derived_sections):
            raise DiceError("파생 계산식이 비어있습니다.")

        base_result = self.roll(base_expr)
        current_values: list[tuple[int | float, str]] = [
            (base_result.value, "기본")
        ]
        derived_results: list[DerivedResult] = []

        for level, formulas_str in enumerate(derived_sections, 1):
            formulas = [f.strip() for f in formulas_str.split(",") if f.strip()]

            if not formulas:
                raise DiceError(f"{level}차 파생에 유효한 계산식이 없습니다.")

            if len(formulas) > MAX_EXPRESSIONS_COUNT:
                raise LimitExceededError(
                    f"{level}차 파생 계산식 제한 ({MAX_EXPRESSIONS_COUNT}개 초과)"
                )

            next_values: list[tuple[int | float, str]] = []

            for source_value, source_label in current_values:
                for formula in formulas:
                    full_expr = f"{source_value}{formula}"
                    try:
                        result = self.roll(full_expr)
                    except DiceError as e:
                        raise DiceError(
                            f"{level}차 파생 계산식 '{formula}' 오류: {e}"
                        )

                    index_in_level = len(next_values) + 1
                    derived_results.append(
                        DerivedResult(
                            formula=formula,
                            full_expression=full_expr,
                            value=result.value,
                            substituted_expression=result.substituted_expression,
                            calculation_steps=result.calculation_steps,
                            level=level,
                            source_label=source_label,
                            source_value=source_value,
                        )
                    )
                    next_values.append((result.value, f"{level}차 #{index_in_level}"))

                    if len(next_values) > MAX_EXPRESSIONS_COUNT:
                        raise LimitExceededError(
                            f"{level}차 파생 결과 제한 ({MAX_EXPRESSIONS_COUNT}개 초과)"
                        )

            current_values = next_values

        return DerivedRollResult(
            base=base_result,
            derived=derived_results,
        )