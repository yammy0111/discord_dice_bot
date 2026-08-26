# tests/test_evaluator.py

import unittest
from dice.tokenizer import Tokenizer
from dice.parser import Parser
from dice.evaluator import Evaluator
from dice.errors import EvaluatorError, LimitExceededError


class TestEvaluator(unittest.TestCase):

    def test_evaluate_simple_dice(self):
        tokens = Tokenizer("1d1 + 5").tokenize()
        tree = Parser(tokens).parse()
        value, rendered, logs = Evaluator().evaluate(tree)

        self.assertEqual(value, 6)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].total, 1)

    def test_division_by_zero(self):
        tokens = Tokenizer("1d6 / 0").tokenize()
        tree = Parser(tokens).parse()
        with self.assertRaises(EvaluatorError):
            Evaluator().evaluate(tree)

    def test_limit_exceeded(self):
        tokens = Tokenizer("1000d6").tokenize()
        tree = Parser(tokens).parse()
        with self.assertRaises(LimitExceededError):
            Evaluator().evaluate(tree)


if __name__ == "__main__":
    unittest.main()
