"""年・月・日の選択とカレンダーポップアップを提供します。"""

import calendar
import tkinter as tk
from datetime import date
from tkinter import ttk

from ui_style import COLORS, FONT


class DatePicker(tk.Frame):
    """A compact year/month/day selector with a popup calendar."""

    def __init__(self, parent, label, initial_date):
        super().__init__(parent, bg=COLORS['white'])
        today = date.today()
        self.minimum_year = max(1900, today.year - 100)
        self.maximum_year = today.year + 10
        self.calendar_popup = None

        tk.Label(
            self, text=label, bg=COLORS['white'], fg=COLORS['text'], font=FONT,
        ).pack(anchor='w', pady=(0, 6))
        row = tk.Frame(self, bg=COLORS['white'])
        row.pack(fill='x')

        self.year_var = tk.StringVar()
        self.month_var = tk.StringVar()
        self.day_var = tk.StringVar()
        year_values = tuple(str(year) for year in range(self.minimum_year, self.maximum_year + 1))
        self.year_box = ttk.Combobox(
            row, textvariable=self.year_var, values=year_values, width=6,
            state='readonly', font=('Yu Gothic UI', 9),
        )
        self.year_box.pack(side='left')
        tk.Label(row, text='年', bg=COLORS['white'], fg=COLORS['muted'], font=FONT).pack(side='left', padx=(3, 7))

        self.month_box = ttk.Combobox(
            row, textvariable=self.month_var, values=tuple(f'{month:02d}' for month in range(1, 13)),
            width=3, state='readonly', font=('Yu Gothic UI', 9),
        )
        self.month_box.pack(side='left')
        tk.Label(row, text='月', bg=COLORS['white'], fg=COLORS['muted'], font=FONT).pack(side='left', padx=(3, 7))

        self.day_box = ttk.Combobox(
            row, textvariable=self.day_var, width=3, state='readonly', font=('Yu Gothic UI', 9),
        )
        self.day_box.pack(side='left')
        tk.Label(row, text='日', bg=COLORS['white'], fg=COLORS['muted'], font=FONT).pack(side='left', padx=(3, 7))
        tk.Button(
            row, text='📅', command=self.open_calendar, bg=COLORS['white'], fg=COLORS['navy'],
            activebackground=COLORS['white'], relief='flat', borderwidth=0, width=3, pady=4,
            cursor='hand2', font=('Segoe UI Emoji', 12),
        ).pack(side='left')

        self.year_box.bind('<<ComboboxSelected>>', self.refresh_days)
        self.month_box.bind('<<ComboboxSelected>>', self.refresh_days)
        self.set_date(initial_date)

    def set_date(self, selected_date):
        if isinstance(selected_date, str):
            selected_date = date.fromisoformat(selected_date)
        selected_date = max(
            date(self.minimum_year, 1, 1),
            min(selected_date, date(self.maximum_year, 12, 31)),
        )
        self.year_var.set(str(selected_date.year))
        self.month_var.set(f'{selected_date.month:02d}')
        self.day_var.set(f'{selected_date.day:02d}')
        self.refresh_days()

    def get_date(self):
        return date(int(self.year_var.get()), int(self.month_var.get()), int(self.day_var.get()))

    def refresh_days(self, _event=None):
        if not self.year_var.get() or not self.month_var.get():
            return
        year = int(self.year_var.get())
        month = int(self.month_var.get())
        day_count = calendar.monthrange(year, month)[1]
        self.day_box.configure(values=tuple(f'{day:02d}' for day in range(1, day_count + 1)))
        if self.day_var.get() and int(self.day_var.get()) > day_count:
            self.day_var.set(f'{day_count:02d}')

    def open_calendar(self):
        if self.calendar_popup is not None and self.calendar_popup.winfo_exists():
            self.calendar_popup.lift()
            return

        selected = self.get_date()
        self.calendar_year = selected.year
        self.calendar_month = selected.month
        popup = tk.Toplevel(self.winfo_toplevel())
        self.calendar_popup = popup
        popup.title('日付を選択')
        x = min(self.winfo_rootx(), popup.winfo_screenwidth() - 300)
        y = self.winfo_rooty() + self.winfo_height()
        if y + 300 > popup.winfo_screenheight():
            y = self.winfo_rooty() - 300
        popup.geometry(f'300x300+{max(0, x)}+{max(0, y)}')
        popup.resizable(False, False)
        popup.transient(self.winfo_toplevel())
        popup.configure(background=COLORS['white'])
        popup.protocol('WM_DELETE_WINDOW', self.close_calendar)

        navigation = tk.Frame(popup, bg=COLORS['white'], padx=12, pady=12)
        navigation.pack(fill='x')
        tk.Button(
            navigation, text='‹', command=lambda: self.shift_calendar(-1),
            bg=COLORS['white'], fg=COLORS['navy'], relief='flat', borderwidth=0,
            font=('Yu Gothic UI', 16, 'bold'), width=3,
        ).pack(side='left')
        self.calendar_title = tk.Label(
            navigation, bg=COLORS['white'], fg=COLORS['navy'],
            font=('Yu Gothic UI', 11, 'bold'),
        )
        self.calendar_title.pack(side='left', expand=True)
        tk.Button(
            navigation, text='›', command=lambda: self.shift_calendar(1),
            bg=COLORS['white'], fg=COLORS['navy'], relief='flat', borderwidth=0,
            font=('Yu Gothic UI', 16, 'bold'), width=3,
        ).pack(side='right')

        weekdays = tk.Frame(popup, bg=COLORS['white'], padx=12)
        weekdays.pack(fill='x')
        for column, weekday in enumerate(('月', '火', '水', '木', '金', '土', '日')):
            tk.Label(
                weekdays, text=weekday, width=4, bg=COLORS['white'],
                fg=COLORS['muted'], font=('Yu Gothic UI', 9, 'bold'),
            ).grid(row=0, column=column, padx=1, pady=4)

        self.calendar_days = tk.Frame(popup, bg=COLORS['white'], padx=12, pady=4)
        self.calendar_days.pack(fill='both', expand=True)
        for column in range(7):
            self.calendar_days.columnconfigure(column, weight=1)
        self.draw_calendar_month()
        popup.grab_set()

    def shift_calendar(self, offset):
        month_index = self.calendar_year * 12 + self.calendar_month - 1 + offset
        year, month_index = divmod(month_index, 12)
        if self.minimum_year <= year <= self.maximum_year:
            self.calendar_year = year
            self.calendar_month = month_index + 1
            self.draw_calendar_month()

    def draw_calendar_month(self):
        self.calendar_title.configure(text=f'{self.calendar_year}年 {self.calendar_month}月')
        for child in self.calendar_days.winfo_children():
            child.destroy()
        selected = self.get_date()
        for row, week in enumerate(calendar.monthcalendar(self.calendar_year, self.calendar_month)):
            for column, day in enumerate(week):
                if day == 0:
                    continue
                is_selected = (
                    self.calendar_year == selected.year
                    and self.calendar_month == selected.month
                    and day == selected.day
                )
                tk.Button(
                    self.calendar_days, text=str(day), width=3,
                    command=lambda value=day: self.choose_calendar_day(value),
                    bg=COLORS['primary'] if is_selected else COLORS['white'],
                    fg=COLORS['white'] if is_selected else COLORS['text'],
                    activebackground=COLORS['primary_active'],
                    activeforeground=COLORS['white'], relief='flat', borderwidth=0,
                    cursor='hand2', font=FONT,
                ).grid(row=row, column=column, padx=1, pady=2, sticky='nsew')

    def choose_calendar_day(self, day):
        self.set_date(date(self.calendar_year, self.calendar_month, day))
        self.close_calendar()

    def close_calendar(self):
        if self.calendar_popup is not None and self.calendar_popup.winfo_exists():
            self.calendar_popup.grab_release()
            self.calendar_popup.destroy()
        self.calendar_popup = None
