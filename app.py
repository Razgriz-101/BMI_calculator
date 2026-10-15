"""アプリ全体の画面遷移、データ連携、BMI入力画面を管理します。"""

import tkinter as tk
from datetime import date
from tkinter import messagebox

from auth_screen import AuthScreen
from bmi_logic import calculate_bmi
from date_picker import DatePicker
from history_editor import HistoryEditor
from history_graph import HistoryGraphPanel
from storage import Storage
from ui_style import COLORS, FONT, create_input_field, make_button


class App(tk.Tk):
    """Coordinates authentication, measurement entry, and history views."""

    def __init__(self, storage=None):
        super().__init__()
        self.storage = storage if storage is not None else Storage()
        self.user_id = None
        self.username = None
        self.configure(background=COLORS['background'])
        self.show_auth_screen()

        remembered_user = self.storage.get_auto_login_user()
        if remembered_user:
            self.after_idle(lambda: self.open_main(*remembered_user))

    def clear_views(self):
        for child in self.winfo_children():
            child.destroy()

    def show_auth_screen(self):
        self.clear_views()
        self.configure(background=COLORS['background'], menu='')
        self.title('BMI計算機 | アカウント')
        self.geometry('540x620')
        self.resizable(False, False)
        self.auth_screen = AuthScreen(self, self.storage, self.open_main)

    def open_main(self, user_id, username):
        self.user_id = user_id
        self.username = username
        self.default_height = self.storage.load_latest_height(user_id)
        self.create_main_screen()

    def logout(self):
        try:
            self.storage.set_auto_login(None)
        except Exception:
            pass
        self.user_id = None
        self.username = None
        self.show_auth_screen()

    def create_main_screen(self):
        self.clear_views()
        self.configure(background=COLORS['background'])
        self.title('BMI計算機')
        self.geometry('1260x760')
        self.resizable(False, False)

        header = tk.Frame(self, bg=COLORS['navy'], padx=28, pady=17)
        header.pack(fill='x')
        heading = tk.Frame(header, bg=COLORS['navy'])
        heading.pack(side='left')
        tk.Label(
            heading, text='BMI', bg=COLORS['primary'], fg=COLORS['white'],
            font=('Yu Gothic UI', 11, 'bold'), padx=9, pady=5,
        ).pack(side='left', padx=(0, 12))
        titles = tk.Frame(heading, bg=COLORS['navy'])
        titles.pack(side='left')
        tk.Label(
            titles, text='BMI計算機', bg=COLORS['navy'], fg=COLORS['white'],
            font=('Yu Gothic UI', 16, 'bold'),
        ).pack(anchor='w')

        account = tk.Frame(header, bg=COLORS['navy'])
        account.pack(side='right')
        tk.Label(
            account, text=self.username, bg=COLORS['navy'], fg=COLORS['white'], font=FONT,
        ).pack(side='left', padx=(0, 12))
        tk.Button(
            account, text='ログアウト', command=self.logout, bg='#263c55', fg=COLORS['white'],
            activebackground='#344c68', activeforeground=COLORS['white'], relief='flat',
            borderwidth=0, padx=12, pady=7, cursor='hand2', font=('Yu Gothic UI', 9),
        ).pack(side='left')

        tabs = tk.Frame(self, bg=COLORS['white'], padx=22, pady=6)
        tabs.pack(fill='x')
        self.page_buttons = {}
        for page_name, label in (
            ('measurement', '計算・グラフ'), ('history', '過去データ'),
        ):
            button = tk.Button(
                tabs, text=label, command=lambda selected=page_name: self.show_main_page(selected),
                relief='flat', borderwidth=0, padx=18, pady=8, cursor='hand2',
                bg=COLORS['background'], fg=COLORS['muted'], font=FONT,
            )
            button.pack(side='left', padx=(0, 8))
            self.page_buttons[page_name] = button

        page_container = tk.Frame(self, bg=COLORS['background'])
        page_container.pack(fill='both', expand=True)
        page_container.rowconfigure(0, weight=1)
        page_container.columnconfigure(0, weight=1)
        self.pages = {
            'measurement': tk.Frame(page_container, bg=COLORS['background']),
            'history': HistoryEditor(
                page_container, self.storage, self.user_id, self.history_was_updated,
            ),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky='nsew')

        content = tk.Frame(self.pages['measurement'], bg=COLORS['background'], padx=22, pady=12)
        content.pack(fill='both', expand=True)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        card = tk.Frame(
            content, bg=COLORS['white'], padx=24, pady=24, width=330,
            highlightthickness=1, highlightbackground=COLORS['border'],
        )
        card.grid(row=0, column=0, sticky='ns', padx=(0, 18))
        card.grid_propagate(False)
        tk.Label(
            card, text='今回の測定', bg=COLORS['white'], fg=COLORS['navy'],
            font=('Yu Gothic UI', 15, 'bold'),
        ).pack(anchor='w')
        tk.Label(
            card, text='身長と体重を入力してください', bg=COLORS['white'],
            fg=COLORS['muted'], font=FONT,
        ).pack(anchor='w', pady=(3, 18))

        self.date_picker = DatePicker(card, '測定日', date.today())
        self.date_picker.pack(fill='x', pady=(0, 14))
        self.height_var = tk.StringVar(
            value='' if self.default_height is None else f'{self.default_height:g}'
        )
        self.weight_var = tk.StringVar()
        self.height_field, self.height_entry = create_input_field(
            card, '身長', 'cm', self.height_var,
        )
        self.height_field.pack(fill='x', pady=(0, 14))
        self.weight_field, self.weight_entry = create_input_field(
            card, '体重', 'kg', self.weight_var,
        )
        self.weight_field.pack(fill='x')
        self.weight_entry.bind('<Return>', lambda _event: self.calculate_and_save())

        result_card = tk.Frame(card, bg=COLORS['soft_blue'], padx=20, pady=16)
        result_card.pack(fill='x', pady=(24, 18))
        tk.Label(
            result_card, text='あなたのBMI', bg=COLORS['soft_blue'],
            fg=COLORS['muted'], font=FONT,
        ).pack(anchor='w')
        self.bmi_result = tk.StringVar(value='—')
        tk.Label(
            result_card, textvariable=self.bmi_result, bg=COLORS['soft_blue'],
            fg=COLORS['navy'], font=('Yu Gothic UI', 30, 'bold'),
        ).pack(anchor='w', pady=(2, 0))
        self.judge = tk.StringVar(value='体重を入力して計算')
        tk.Label(
            result_card, textvariable=self.judge, bg=COLORS['soft_blue'],
            fg=COLORS['primary_active'], font=('Yu Gothic UI', 12, 'bold'),
        ).pack(anchor='w', pady=(2, 0))
        make_button(card, '計算して保存', self.calculate_and_save, primary=True).pack(fill='x')
        tk.Label(
            card, text='計算結果は履歴グラフへ自動で反映されます。', bg=COLORS['white'],
            fg=COLORS['muted'], font=('Yu Gothic UI', 9), wraplength=260, justify='left',
        ).pack(anchor='w', pady=(14, 0))
        self.height_entry.focus_set()

        self.graph_panel = HistoryGraphPanel(content)
        self.graph_panel.grid(row=0, column=1, sticky='nsew')
        self.refresh_history_graph()
        self.show_main_page('measurement')

    def show_main_page(self, page_name):
        self.pages[page_name].tkraise()
        self.current_page_name = page_name
        for name, button in self.page_buttons.items():
            selected = name == page_name
            button.configure(
                bg=COLORS['soft_blue'] if selected else COLORS['background'],
                fg=COLORS['primary_active'] if selected else COLORS['muted'],
                font=('Yu Gothic UI', 10, 'bold' if selected else 'normal'),
            )

    def calculate_and_save(self):
        try:
            measured_date = self.date_picker.get_date().isoformat()
            height = float(self.height_var.get())
            weight = float(self.weight_var.get())
            bmi, category = calculate_bmi(height, weight)
        except (ValueError, ZeroDivisionError, OverflowError, tk.TclError):
            self.bmi_result.set('入力エラー')
            self.judge.set('日付・身長・体重を正しく入力してください')
            return

        self.bmi_result.set(f'{bmi:.3f}')
        self.judge.set(category)
        try:
            self.storage.save_history(self.user_id, measured_date, height, weight, bmi)
        except Exception as error:
            messagebox.showerror(
                '保存エラー', f'計算結果を履歴に保存できませんでした。\n{error}', parent=self,
            )
            return
        self.default_height = self.storage.load_latest_height(self.user_id)
        self.refresh_history_graph()

    def refresh_history_graph(self):
        try:
            records = self.storage.load_history(self.user_id)
        except Exception as error:
            messagebox.showerror('読み込みエラー', f'履歴を読み込めませんでした。\n{error}', parent=self)
            records = []
        self.graph_panel.set_records(records)

    def history_was_updated(self, previous_default):
        current_height = self.height_var.get().strip()
        try:
            self.default_height = self.storage.load_latest_height(self.user_id)
        except Exception as error:
            messagebox.showerror('履歴エラー', f'最新の身長を読み込めませんでした。\n{error}', parent=self)
            return
        if previous_default is not None and current_height == f'{previous_default:g}':
            self.height_var.set(
                '' if self.default_height is None else f'{self.default_height:g}'
            )
        self.refresh_history_graph()


def main():
    """BMI計算アプリを起動します。"""
    app = App()
    app.mainloop()
