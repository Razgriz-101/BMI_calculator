"""BMIと身長・体重の推移を表示するグラフパネルです。"""

import math
import tkinter as tk
from datetime import datetime

from bmi_logic import BMI_ZONES
from ui_style import COLORS


class HistoryGraphPanel(tk.Frame):
    """Always-visible BMI and measurement trend charts."""

    def __init__(self, parent):
        super().__init__(
            parent, bg=COLORS['white'], padx=18, pady=18,
            highlightthickness=1, highlightbackground=COLORS['border'],
        )
        self.records = []
        tk.Label(
            self, text='BMIの推移', bg=COLORS['white'], fg=COLORS['navy'],
            font=('Yu Gothic UI', 15, 'bold'),
        ).pack(anchor='w')
        tk.Label(
            self, text='過去の測定履歴', bg=COLORS['white'],
            fg=COLORS['muted'], font=('Yu Gothic UI', 9),
        ).pack(anchor='w', pady=(2, 12))

        graph_body = tk.Frame(self, bg=COLORS['white'])
        graph_body.pack(fill='both', expand=True)
        chart_stack = tk.Frame(graph_body, bg=COLORS['white'])
        chart_stack.pack(side='left', fill='both', expand=True)

        bmi_panel = tk.Frame(chart_stack, bg=COLORS['white'])
        bmi_panel.pack(fill='both', expand=True, pady=(0, 6))
        tk.Label(
            bmi_panel, text='BMI', bg=COLORS['white'], fg=COLORS['muted'],
            font=('Yu Gothic UI', 9, 'bold'),
        ).pack(anchor='w')
        self.bmi_canvas = tk.Canvas(bmi_panel, background=COLORS['white'], highlightthickness=0)
        self.bmi_canvas.pack(fill='both', expand=True)

        measurement_panel = tk.Frame(chart_stack, bg=COLORS['white'])
        measurement_panel.pack(fill='both', expand=True, pady=(6, 0))
        tk.Label(
            measurement_panel, text='身長（左・cm）／体重（右・kg）',
            bg=COLORS['white'], fg=COLORS['muted'], font=('Yu Gothic UI', 9, 'bold'),
        ).pack(anchor='w')
        self.measurement_canvas = tk.Canvas(
            measurement_panel, background=COLORS['white'], highlightthickness=0,
        )
        self.measurement_canvas.pack(fill='both', expand=True)

        self._create_legend(graph_body)
        self.bmi_canvas.bind('<Configure>', self.draw_bmi)
        self.measurement_canvas.bind('<Configure>', self.draw_measurements)

    def _create_legend(self, parent):
        legend = tk.Frame(parent, padx=12, pady=12, width=390, bg=COLORS['white'])
        legend.pack(side='right', fill='y', padx=(14, 0))
        legend.pack_propagate(False)
        tk.Label(
            legend, text='BMI区分', font=('Yu Gothic UI', 11, 'bold'),
            bg=COLORS['white'], fg=COLORS['navy'],
        ).pack(anchor='w', pady=(0, 8))
        for _, _, color, label in BMI_ZONES:
            item = tk.Frame(legend, bg=COLORS['white'])
            item.pack(fill='x', anchor='w', pady=4)
            tk.Label(
                item, width=2, height=1, background=color, relief='solid', bd=1,
            ).pack(side='left', padx=(0, 8))
            tk.Label(
                item, text=label, justify='left', anchor='w',
                font=('Yu Gothic UI', 9), bg=COLORS['white'], fg=COLORS['text'],
            ).pack(side='left', fill='x', expand=True)

        tk.Label(
            legend, text='グラフの線', font=('Yu Gothic UI', 10, 'bold'),
            bg=COLORS['white'], fg=COLORS['navy'],
        ).pack(anchor='w', pady=(12, 6))
        for color, label in (
            (COLORS['primary'], 'BMI'), ('#0f766e', '身長（cm）'), ('#ea580c', '体重（kg）'),
        ):
            item = tk.Frame(legend, bg=COLORS['white'])
            item.pack(fill='x', anchor='w', pady=3)
            tk.Label(item, width=2, height=1, background=color, relief='solid', bd=1).pack(
                side='left', padx=(0, 8),
            )
            tk.Label(
                item, text=label, anchor='w', font=('Yu Gothic UI', 9),
                bg=COLORS['white'], fg=COLORS['text'],
            ).pack(side='left')

    def set_records(self, records):
        self.records = records
        self.draw_bmi()
        self.draw_measurements()

    @staticmethod
    def _date_tick_indices(count, maximum=4):
        label_count = min(count, maximum)
        return sorted({
            round(index * (count - 1) / max(label_count - 1, 1))
            for index in range(label_count)
        })

    @staticmethod
    def _format_month(value):
        measured_at = datetime.fromisoformat(value)
        if measured_at.tzinfo is not None:
            measured_at = measured_at.astimezone()
        return measured_at.strftime('%Y/%m')

    def draw_bmi(self, _event=None):
        canvas = self.bmi_canvas
        canvas.delete('all')
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if width < 140 or height < 100:
            return
        if not self.records:
            canvas.create_text(
                width / 2, height / 2, text='測定履歴がありません',
                fill=COLORS['muted'], font=('Yu Gothic UI', 11),
            )
            return

        left, right, top, bottom = 52, width - 12, 12, height - 38
        if right <= left or bottom <= top:
            return
        values = [record[1] for record in self.records]
        low = math.floor(min(values) - 1)
        high = math.ceil(max(values) + 1)
        if low == high:
            low -= 1
            high += 1

        def value_to_y(value):
            return bottom - (value - low) / (high - low) * (bottom - top)

        for lower, upper, color, _ in BMI_ZONES:
            zone_low = low if lower is None else max(low, lower)
            zone_high = high if upper is None else min(high, upper)
            if zone_low < zone_high:
                canvas.create_rectangle(
                    left, value_to_y(zone_high), right, value_to_y(zone_low),
                    fill=color, outline='',
                )
        for tick in range(5):
            value = low + (high - low) * tick / 4
            y = value_to_y(value)
            canvas.create_line(left, y, right, y, fill='#dbe3ed')
            canvas.create_text(
                left - 8, y, text=f'{value:.1f}', anchor='e',
                fill=COLORS['muted'], font=('Yu Gothic UI', 9),
            )

        count = len(self.records)
        points = []
        for index, record in enumerate(self.records):
            x = left + (right - left) * index / max(count - 1, 1)
            points.extend((x, value_to_y(record[1])))
        if count > 1:
            canvas.create_line(*points, fill=COLORS['primary'], width=2, smooth=True)
        for index in range(count):
            x, y = points[index * 2:index * 2 + 2]
            canvas.create_oval(
                x - 4, y - 4, x + 4, y + 4,
                fill=COLORS['primary'], outline=COLORS['white'],
            )
        for index in self._date_tick_indices(count):
            x = left + (right - left) * index / max(count - 1, 1)
            canvas.create_text(
                x, bottom + 12, text=self._format_month(self.records[index][0]),
                anchor='n', fill=COLORS['muted'], font=('Yu Gothic UI', 9),
            )

    def draw_measurements(self, _event=None):
        canvas = self.measurement_canvas
        canvas.delete('all')
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if width < 150 or height < 100:
            return
        if not self.records:
            canvas.create_text(
                width / 2, height / 2, text='測定履歴がありません',
                fill=COLORS['muted'], font=('Yu Gothic UI', 10),
            )
            return

        left, right, top, bottom = 48, width - 48, 12, height - 38
        if right <= left or bottom <= top:
            return
        heights = [record[2] for record in self.records]
        weights = [record[3] for record in self.records]

        def padded_range(values):
            minimum, maximum = min(values), max(values)
            padding = max((maximum - minimum) * 0.15, 0.5)
            return minimum - padding, maximum + padding

        height_low, height_high = padded_range(heights)
        weight_low, weight_high = padded_range(weights)

        def y_for(value, low, high):
            return bottom - (value - low) / (high - low) * (bottom - top)

        for tick in range(5):
            fraction = tick / 4
            y = bottom - fraction * (bottom - top)
            height_value = height_low + fraction * (height_high - height_low)
            weight_value = weight_low + fraction * (weight_high - weight_low)
            canvas.create_line(left, y, right, y, fill='#dbe3ed')
            canvas.create_text(
                left - 6, y, text=f'{height_value:.1f}', anchor='e',
                fill='#0f766e', font=('Yu Gothic UI', 8),
            )
            canvas.create_text(
                right + 6, y, text=f'{weight_value:.1f}', anchor='w',
                fill='#ea580c', font=('Yu Gothic UI', 8),
            )

        count = len(self.records)
        height_points, weight_points = [], []
        for index, record in enumerate(self.records):
            x = left + (right - left) * index / max(count - 1, 1)
            height_points.extend((x, y_for(record[2], height_low, height_high)))
            weight_points.extend((x, y_for(record[3], weight_low, weight_high)))
        if count > 1:
            canvas.create_line(*height_points, fill='#0f766e', width=2, smooth=True)
            canvas.create_line(*weight_points, fill='#ea580c', width=2, smooth=True)
        for index in range(count):
            height_x, height_y = height_points[index * 2:index * 2 + 2]
            weight_x, weight_y = weight_points[index * 2:index * 2 + 2]
            canvas.create_oval(
                height_x - 3, height_y - 3, height_x + 3, height_y + 3,
                fill='#0f766e', outline=COLORS['white'],
            )
            canvas.create_oval(
                weight_x - 3, weight_y - 3, weight_x + 3, weight_y + 3,
                fill='#ea580c', outline=COLORS['white'],
            )
        for index in self._date_tick_indices(count):
            x = left + (right - left) * index / max(count - 1, 1)
            canvas.create_text(
                x, bottom + 11, text=self._format_month(self.records[index][0]),
                anchor='n', fill=COLORS['muted'], font=('Yu Gothic UI', 8),
            )
