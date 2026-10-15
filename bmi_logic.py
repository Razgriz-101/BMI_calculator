"""BMIの計算式、区分、カテゴリ判定をまとめます。"""

import math


JUDGE_LIST = [
    '低体重（痩せすぎ）', '低体重（痩せ）', '低体重（痩せぎみ）', '普通体重',
    '肥満予備軍（過体重）', '肥満（1度）', '肥満（2度）', '肥満（3度）',
]

BMI_ZONES = [
    (None, 16.0, '#e8ecff', 'BMI < 16.0　低体重（痩せすぎ）'),
    (16.0, 17.0, '#dceaff', '16.0 ≤ BMI < 17.0　低体重（痩せ）'),
    (17.0, 18.5, '#d9f0ff', '17.0 ≤ BMI < 18.5　低体重（痩せぎみ）'),
    (18.5, 25.0, '#e3f5e8', '18.5 ≤ BMI < 25.0　普通体重'),
    (25.0, 30.0, '#fff3c4', '25.0 ≤ BMI < 30.0　肥満予備軍（過体重）'),
    (30.0, 35.0, '#ffe3c2', '30.0 ≤ BMI < 35.0　肥満（1度）'),
    (35.0, 40.0, '#ffd8d8', '35.0 ≤ BMI < 40.0　肥満（2度）'),
    (40.0, None, '#f7c6d0', 'BMI ≥ 40.0　肥満（3度）'),
]


def calculate_bmi(height_cm, weight_kg):
    """身長(cm)と体重(kg)からBMI値と判定区分を返します。"""
    if not math.isfinite(height_cm) or not math.isfinite(weight_kg):
        raise ValueError('身長と体重には有限の数値を指定してください。')
    if height_cm <= 0 or weight_kg <= 0:
        raise ValueError('身長と体重には正の数値を指定してください。')

    bmi = weight_kg / (height_cm / 100) ** 2
    if not math.isfinite(bmi):
        raise ValueError('BMIを計算できません。')

    for index, (lower, upper, _, _) in enumerate(BMI_ZONES):
        if (lower is None or bmi >= lower) and (upper is None or bmi < upper):
            return bmi, JUDGE_LIST[index]
    raise ValueError('BMIの区分を判定できません。')
