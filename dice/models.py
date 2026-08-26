# dice/models.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RollEntry:
    """개별 주사위 굴림 결과"""
    expression: str
    rolls: list[int]
    total: int


@dataclass(slots=True)
class EvalResult:
    """AST 평가 내부 중간 결과"""
    value: int | float
    rendered: str
    op_type: str | None = None


@dataclass(slots=True)
class EvaluationContext:
    """주사위 평가 실행 컨텍스트 (총 굴림 수 한도 및 로그 관리)"""
    roll_entries: list[RollEntry]
    total_roll_count: int = 0


@dataclass(slots=True)
class RenderResult:
    """단계별 연산 풀이 렌더링 결과"""
    substituted: str
    steps: list[str]
    result: str


@dataclass(slots=True)
class EngineResult:
    """DiceEngine 최종 실행 결과"""
    expression: str
    value: int | float
    substituted_expression: str
    calculation_steps: list[str]
    roll_logs: list[RollEntry]
    render_result: RenderResult


@dataclass(slots=True)
class DerivedResult:
    """파생 계산 결과 (하나의 주사위 값에서 파생된 추가 계산)"""
    formula: str
    full_expression: str
    value: int | float
    substituted_expression: str
    calculation_steps: list[str]


@dataclass(slots=True)
class DerivedRollResult:
    """주사위 기본 굴림 + 파생 계산 결과 묶음"""
    base: EngineResult
    derived: list[DerivedResult]
