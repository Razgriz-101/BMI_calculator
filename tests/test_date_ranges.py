"""Tests for date presets and date-based record filtering."""

import unittest
from datetime import date

from date_ranges import (
    filter_records_by_date,
    period_range,
    stored_date_to_local,
    subtract_months,
)


class DateRangesTests(unittest.TestCase):
    def test_week_period_includes_seven_calendar_days(self):
        start, end = period_range('1週間', date(2026, 3, 12))
        self.assertEqual(start, date(2026, 3, 6))
        self.assertEqual(end, date(2026, 3, 12))
        self.assertEqual((end - start).days + 1, 7)

    def test_month_subtraction_clamps_to_destination_month(self):
        self.assertEqual(subtract_months(date(2025, 3, 31), 1), date(2025, 2, 28))
        self.assertEqual(subtract_months(date(2024, 3, 31), 1), date(2024, 2, 29))

    def test_unknown_period_has_no_preset_range(self):
        self.assertIsNone(period_range('すべて', date(2026, 3, 12)))

    def test_filter_includes_both_endpoints_and_uses_requested_date_column(self):
        records = [
            (1, '2026-03-05', 165.0),
            (2, '2026-03-06', 166.0),
            (3, '2026-03-12', 167.0),
            (4, '2026-03-13', 168.0),
        ]
        selected = filter_records_by_date(
            records, date(2026, 3, 6), date(2026, 3, 12), date_index=1,
        )
        self.assertEqual([record[0] for record in selected], [2, 3])

    def test_filter_returns_empty_for_reversed_range(self):
        self.assertEqual(
            filter_records_by_date([], date(2026, 3, 12), date(2026, 3, 6)),
            [],
        )

    def test_iso_date_string_is_read_as_local_date(self):
        self.assertEqual(stored_date_to_local('2026-03-12'), date(2026, 3, 12))


if __name__ == '__main__':
    unittest.main()
