# tests/test_mackerel.py

import unittest
from dice.mackerel import calculate_mackerel_probabilities, roll_mackerel_dice


class TestMackerelDice(unittest.TestCase):
    def test_20_sides_low_bias(self):
        probs = calculate_mackerel_probabilities(20, "낮은 수")
        self.assertEqual(len(probs), 20)
        self.assertAlmostEqual(sum(probs), 1.0, places=7)

        # 양 끝단 비율 4:1 (w(1)=4, w(20)=1)
        self.assertAlmostEqual(probs[0] / probs[19], 4.0, places=5)

        # 단조 감소 확인 (x가 커질수록 확률 감소)
        for i in range(len(probs) - 1):
            self.assertGreaterEqual(probs[i], probs[i + 1])

        # 위로 볼록(concave) 곡률 확인: 기울기 변화율(2계 차분)이 음수
        # f(x+1) - 2f(x) + f(x-1) <= 0
        for i in range(1, len(probs) - 1):
            second_diff = probs[i + 1] - 2 * probs[i] + probs[i - 1]
            self.assertLessEqual(second_diff, 1e-6)

    def test_20_sides_high_bias(self):
        probs = calculate_mackerel_probabilities(20, "높은 수")
        self.assertEqual(len(probs), 20)
        self.assertAlmostEqual(sum(probs), 1.0, places=7)

        # 양 끝단 비율 4:1 (w(20)=4, w(1)=1)
        self.assertAlmostEqual(probs[19] / probs[0], 4.0, places=5)

        # 단조 증가 확인 (x가 커질수록 확률 증가)
        for i in range(len(probs) - 1):
            self.assertLessEqual(probs[i], probs[i + 1])

        # 위로 볼록(concave) 곡률 확인: 기울기 변화율이 음수
        for i in range(1, len(probs) - 1):
            second_diff = probs[i + 1] - 2 * probs[i] + probs[i - 1]
            self.assertLessEqual(second_diff, 1e-6)

    def test_roll_mackerel_range(self):
        for _ in range(100):
            res = roll_mackerel_dice(sides=20, bias="높은 수")
            self.assertGreaterEqual(res.result, 1)
            self.assertLessEqual(res.result, 20)
            self.assertGreaterEqual(res.prob_percent, 1.0)
            self.assertLessEqual(res.prob_percent, 7.0)

    def test_general_n_sides(self):
        for n in [3, 4, 6, 10, 100]:
            probs_low = calculate_mackerel_probabilities(n, "낮은 수")
            self.assertEqual(len(probs_low), n)
            self.assertAlmostEqual(sum(probs_low), 1.0, places=6)
            self.assertAlmostEqual(probs_low[0] / probs_low[-1], 4.0, places=5)

            probs_high = calculate_mackerel_probabilities(n, "높은 수")
            self.assertEqual(len(probs_high), n)
            self.assertAlmostEqual(sum(probs_high), 1.0, places=6)
            self.assertAlmostEqual(probs_high[-1] / probs_high[0], 4.0, places=5)


    def test_engine_mackerel_expression_roll(self):
        from dice.engine import DiceEngine
        engine = DiceEngine()
        
        # 기본 표현식 연산 테스트
        result = engine.roll("1d20 + 5", bias="높은 수")
        self.assertEqual(result.expression, "1d20 + 5")
        self.assertGreaterEqual(result.value, 6)
        self.assertLessEqual(result.value, 25)
        self.assertEqual(len(result.roll_logs), 1)

        # 다중 표현식 테스트
        results = engine.roll_multiple("1d20, 2d6+3", bias="낮은 수")
        self.assertEqual(len(results), 2)

        # 파생 표현식 테스트
        derived = engine.roll_derived("1d20 > +5, *2", bias="높은 수")
        self.assertEqual(len(derived.derived), 2)
        self.assertEqual(derived.derived[0].value, derived.base.value + 5)
        self.assertEqual(derived.derived[1].value, derived.base.value * 2)


if __name__ == "__main__":
    unittest.main()

