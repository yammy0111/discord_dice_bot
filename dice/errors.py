# dice/errors.py

from __future__ import annotations


class DiceError(Exception):
    """주사위 엔진 기본 예외 클래스"""
    pass


class TokenizerError(DiceError):
    """토크나이저 어휘 분석 에러"""
    pass


class ParserError(DiceError):
    """파서 구문 분석 에러"""
    pass


class EvaluatorError(DiceError):
    """평가기 실행 에러"""
    pass


class LimitExceededError(EvaluatorError):
    """제한 한도 초과 에러"""
    pass
