# tests/test_tokenizer.py

import unittest
from dice.tokenizer import Tokenizer, TokenType, TokenizerError


class TestTokenizer(unittest.TestCase):

    def test_basic_expression(self):
        expr = "((1d3+1d2)+2d5)**2/3"
        tokens = Tokenizer(expr).tokenize()
        
        self.assertGreater(len(tokens), 0)
        self.assertEqual(tokens[-1].type, TokenType.EOF)

    def test_dice_token(self):
        tokens = Tokenizer("2d20").tokenize()
        expected = [
            (TokenType.NUMBER, "2"),
            (TokenType.D, "d"),
            (TokenType.NUMBER, "20"),
            (TokenType.EOF, ""),
        ]
        actual = [(t.type, t.value) for t in tokens]
        self.assertEqual(actual, expected)

    def test_invalid_character(self):
        with self.assertRaises(TokenizerError):
            Tokenizer("2d20 @ 5").tokenize()


if __name__ == "__main__":
    unittest.main()