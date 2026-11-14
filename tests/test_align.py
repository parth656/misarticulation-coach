import unittest

from core.align import accuracy, align_phonemes


class PhonemeAccuracyTests(unittest.TestCase):
    def test_perfect_match_scores_one(self):
        ops = align_phonemes(["p", "æ", "t"], ["p", "æ", "t"])
        self.assertEqual(accuracy(ops), 1.0)

    def test_substitution_reduces_score(self):
        ops = align_phonemes(["r", "æ", "t"], ["w", "æ", "t"])
        self.assertAlmostEqual(accuracy(ops), 2 / 3)

    def test_omission_reduces_score(self):
        ops = align_phonemes(["θ", "ʌ", "m"], ["ʌ", "m"])
        self.assertAlmostEqual(accuracy(ops), 2 / 3)

    def test_insertion_reduces_score(self):
        ops = align_phonemes(["p", "t"], ["p", "ə", "t"])
        self.assertAlmostEqual(accuracy(ops), 2 / 3)

    def test_empty_alignment_scores_zero(self):
        self.assertEqual(accuracy([]), 0.0)


if __name__ == "__main__":
    unittest.main()
