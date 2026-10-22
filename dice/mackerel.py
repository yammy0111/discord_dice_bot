# dice/mackerel.py

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Literal

BiasType = Literal["높은 수", "낮은 수"]


@dataclass
class MackerelRollResult:
    """간고등어 주사위 굴림 결과"""
    sides: int
    bias: BiasType
    result: int
    prob_percent: float
    weights: list[float]


def calculate_mackerel_probabilities(sides: int, bias: BiasType) -> list[float]:
    """
    주사위 눈 수(sides)와 보정 방향(bias: '높은 수' 또는 '낮은 수')에 따른
    확률 분포(로그 함수 변형 꼴의 위로 볼록한 곡선)를 계산합니다.
    
    특징:
    - 위로 볼록(concave)한 곡선 형태로, 기존 아래로 볼록한 2차 곡선에 비해
      중간값(중간 눈금대)이 등장할 확률 비중이 더 높게 보정됩니다.
    - 높은 수 보정: 눈금이 올라갈수록 확률이 로그 함수처럼 가파르게 상승한 뒤 완만해집니다.
    - 낮은 수 보정: 높은 수 보정의 좌우 대칭으로, 낮은 눈금대에서 높은 확률을 유지하다가
      큰 눈금대로 갈수록 가파르게 감소합니다.
    - 양 끝단 가중치 비는 4:1(최대 4배)을 유지합니다.
    """
    if sides < 1:
        raise ValueError("주사위 면 수는 1 이상이어야 합니다.")
    if sides == 1:
        return [1.0]
    if sides == 2:
        return [0.75, 0.25] if bias == "낮은 수" else [0.25, 0.75]

    n = sides
    # 양 끝값 가중치 비를 4:1로 맞추는 alpha (w(1)=1, w(N)=4)
    alpha = 3.0 / math.log(n)
    raw_weights: list[float] = []

    for x in range(1, n + 1):
        # 높은 수 보정은 x가 클수록 가중치 증가, 낮은 수 보정은 대칭
        k = x if bias == "높은 수" else (n + 1 - x)
        w = 1.0 + alpha * math.log(k)
        raw_weights.append(w)

    total_weight = sum(raw_weights)
    return [w / total_weight for w in raw_weights]



def roll_mackerel_dice(sides: int = 20, bias: BiasType = "높은 수") -> MackerelRollResult:
    """
    간고등어 주사위를 굴립니다.
    """
    if sides < 1:
        raise ValueError("주사위 면 수는 1 이상이어야 합니다.")

    weights = calculate_mackerel_probabilities(sides, bias)
    outcomes = list(range(1, sides + 1))
    rolled = random.choices(outcomes, weights=weights, k=1)[0]
    prob_percent = weights[rolled - 1] * 100.0

    return MackerelRollResult(
        sides=sides,
        bias=bias,
        result=rolled,
        prob_percent=prob_percent,
        weights=weights,
    )
