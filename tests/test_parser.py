# tests/test_parser.py

import unittest
from dice.tokenizer import Tokenizer
from dice.parser import Parser, ParserError
from dice.nodes import BinaryOpNode, DiceNode, NumberNode


class TestParser(unittest.TestCase):

    def test_parse_dice_and_math(self):
        tokens = Tokenizer("1d6 + 5").tokenize()
        tree = Parser(tokens).parse()

        self.assertIsInstance(tree, BinaryOpNode)
        assert isinstance(tree, BinaryOpNode)

        self.assertEqual(tree.operator, "+")

        self.assertIsInstance(tree.left, DiceNode)
        assert isinstance(tree.left, DiceNode)
        self.assertEqual(tree.left.count, 1)
        self.assertEqual(tree.left.sides, 6)

        self.assertIsInstance(tree.right, NumberNode)
        assert isinstance(tree.right, NumberNode)
        self.assertEqual(tree.right.value, 5)

    def test_parse_default_dice_count(self):
        tokens = Tokenizer("d20").tokenize()
        tree = Parser(tokens).parse()

        self.assertIsInstance(tree, DiceNode)
        assert isinstance(tree, DiceNode)
        self.assertEqual(tree.count, 1)
        self.assertEqual(tree.sides, 20)

    def test_parse_syntax_error(self):
        tokens = Tokenizer("1d6 +").tokenize()
        with self.assertRaises(ParserError):
            Parser(tokens).parse()


if __name__ == "__main__":
    unittest.main()