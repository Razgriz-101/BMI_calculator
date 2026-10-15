"""Tests for BMI calculation and category boundaries."""

import unittest

from bmi_logic import JUDGE_LIST, calculate_bmi


class CalculateBmiTests(unittest.TestCase):
    def test_category_boundaries(self):
        cases = (
            (15.999, JUDGE_LIST[0]),
            (16.0, JUDGE_LIST[1]),
            (17.0, JUDGE_LIST[2]),
            (18.5, JUDGE_LIST[3]),
            (25.0, JUDGE_LIST[4]),
            (30.0, JUDGE_LIST[5]),
            (35.0, JUDGE_LIST[6]),
            (40.0, JUDGE_LIST[7]),
        )
        for expected_bmi, expected_category in cases:
            with self.subTest(bmi=expected_bmi):
                bmi, category = calculate_bmi(100.0, expected_bmi)
                self.assertAlmostEqual(bmi, expected_bmi)
                self.assertEqual(category, expected_category)

    def test_calculates_using_centimeters(self):
        bmi, category = calculate_bmi(170.0, 65.0)
        self.assertAlmostEqual(bmi, 65.0 / (1.7 ** 2))
        self.assertEqual(category, JUDGE_LIST[3])

    def test_rejects_nonpositive_or_nonfinite_measurements(self):
        cases = (
            (0.0, 50.0),
            (-1.0, 50.0),
            (170.0, 0.0),
            (170.0, -1.0),
            (float('nan'), 50.0),
            (170.0, float('inf')),
        )
        for height, weight in cases:
            with self.subTest(height=height, weight=weight):
                with self.assertRaises(ValueError):
                    calculate_bmi(height, weight)


if __name__ == '__main__':
    unittest.main()
