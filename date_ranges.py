"""グラフと履歴一覧で共有する日付期間の計算処理。"""

import calendar
from datetime import date, datetime, timedelta


PERIOD_OPTIONS = ('1週間', '1か月', '3か月', '6か月', '1年')


def subtract_months(value, months):
    """月数を戻し、移動先の月に同じ日がなければ月末に合わせます。"""
    month_index = value.year * 12 + value.month - 1 - months
    year, month_index = divmod(month_index, 12)
    month = month_index + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def period_range(period, today=None):
    """期間名から今日を含む開始日・終了日を返します。"""
    today = today or date.today()
    if period == '1週間':
        return today - timedelta(days=6), today
    if period == '1か月':
        return subtract_months(today, 1), today
    if period == '3か月':
        return subtract_months(today, 3), today
    if period == '6か月':
        return subtract_months(today, 6), today
    if period == '1年':
        return subtract_months(today, 12), today
    return None


def stored_date_to_local(value):
    """SQLiteの測定日文字列をローカル日付に変換します。"""
    measured_at = datetime.fromisoformat(value)
    if measured_at.tzinfo is not None:
        measured_at = measured_at.astimezone()
    return measured_at.date()


def filter_records_by_date(records, start, end, date_index=0):
    """日付範囲の両端を含めてレコードを抽出します。"""
    if start > end:
        return []
    return [
        record for record in records
        if start <= stored_date_to_local(record[date_index]) <= end
    ]
