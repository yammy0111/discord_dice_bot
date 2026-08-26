# dice/nodes.py

from __future__ import annotations

from dataclasses import dataclass


class ASTNode:
    pass


@dataclass(slots=True)
class NumberNode(ASTNode):
    value: int | float


@dataclass(slots=True)
class DiceNode(ASTNode):
    count: int
    sides: int


@dataclass(slots=True)
class UnaryOpNode(ASTNode):
    operator: str
    operand: ASTNode


@dataclass(slots=True)
class BinaryOpNode(ASTNode):
    left: ASTNode
    operator: str
    right: ASTNode


@dataclass(slots=True)
class PercentNode(ASTNode):
    """후위 % (백분율) 노드 (예: 50% -> 0.5)"""
    operand: ASTNode