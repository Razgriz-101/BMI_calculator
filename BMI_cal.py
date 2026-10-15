import calendar
import hashlib
import hmac
import math
import os
import secrets
import sqlite3
import tkinter as tk
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path
from tkinter import messagebox, ttk


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

COLORS = {
    'background': '#f3f6fb',
    'white': '#ffffff',
    'navy': '#142a43',
    'primary': '#2563eb',
    'primary_active': '#1d4ed8',
    'text': '#1f2937',
    'muted': '#64748b',
    'border': '#d8e0ea',
    'soft_blue': '#eff6ff',
    'error': '#b42318',
}

FONT = ('Yu Gothic UI', 10)


class DatePicker(tk.Frame):
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
        values = tuple(f'{day:02d}' for day in range(1, day_count + 1))
        self.day_box.configure(values=values)
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


class App(tk.Tk):
    PBKDF2_ITERATIONS = 600_000

    def __init__(self):
        super().__init__()
        self.history_db = self.get_history_db_path()
        self.user_id = None
        self.username = None
        self.initialize_database()
        self.configure(background=COLORS['background'])
        self.show_auth_screen()

        remembered_user = self.get_auto_login_user()
        if remembered_user:
            self.after_idle(lambda: self.open_main(*remembered_user))

    @staticmethod
    def get_history_db_path():
        if os.name == 'nt':
            data_dir = Path(os.environ.get('LOCALAPPDATA') or Path.home() / 'AppData' / 'Local')
        else:
            data_dir = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local' / 'share')
        return data_dir / 'BMI_calculator' / 'bmi_history.sqlite3'

    @staticmethod
    def ensure_history_table(connection):
        connection.execute(
            '''CREATE TABLE IF NOT EXISTS bmi_history (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER,
                   measured_at TEXT NOT NULL,
                   height_cm REAL NOT NULL,
                   weight_kg REAL NOT NULL,
                   bmi REAL NOT NULL,
                   is_sample INTEGER NOT NULL DEFAULT 0
               )'''
        )
        columns = {row[1] for row in connection.execute('PRAGMA table_info(bmi_history)')}
        if 'user_id' not in columns:
            connection.execute('ALTER TABLE bmi_history ADD COLUMN user_id INTEGER')
        if 'is_sample' not in columns:
            connection.execute(
                'ALTER TABLE bmi_history ADD COLUMN is_sample INTEGER NOT NULL DEFAULT 0'
            )

    def initialize_database(self):
        self.history_db.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.history_db)) as connection, connection:
            connection.execute(
                '''CREATE TABLE IF NOT EXISTS users (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                       password_salt BLOB NOT NULL,
                       password_hash BLOB NOT NULL,
                       password_iterations INTEGER NOT NULL,
                       created_at TEXT NOT NULL
                   )'''
            )
            connection.execute(
                '''CREATE TABLE IF NOT EXISTS app_settings (
                       setting_key TEXT PRIMARY KEY,
                       setting_value TEXT NOT NULL
                   )'''
            )
            self.ensure_history_table(connection)

    def seed_sample_history(self, user_id):
        with closing(sqlite3.connect(self.history_db)) as connection, connection:
            self.ensure_history_table(connection)
            count = connection.execute(
                'SELECT COUNT(*) FROM bmi_history WHERE user_id = ?', (user_id,)
            ).fetchone()[0]
            if count:
                return

            current_month = datetime.now(timezone.utc)
            first_month_index = current_month.year * 12 + current_month.month - 1 - 59
            records = []
            for index in range(60):
                year, month_index = divmod(first_month_index + index, 12)
                month = month_index + 1
                weight = round(
                    70.0 - 4.0 * index / 59 + 0.6 * math.sin(index * 2 * math.pi / 12), 1,
                )
                measured_at = datetime(year, month, 1, 12, tzinfo=timezone.utc)
                records.append((
                    user_id, measured_at.isoformat(timespec='seconds'), 170.0,
                    weight, weight / (1.7 ** 2), 1,
                ))

            connection.executemany(
                '''INSERT INTO bmi_history
                   (user_id, measured_at, height_cm, weight_kg, bmi, is_sample)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                records,
            )

    @staticmethod
    def hash_password(password, salt):
        return hashlib.pbkdf2_hmac(
            'sha256', password.encode('utf-8'), salt, App.PBKDF2_ITERATIONS,
        )

    def create_account(self, username, password):
        salt = secrets.token_bytes(16)
        password_hash = self.hash_password(password, salt)
        with closing(sqlite3.connect(self.history_db)) as connection, connection:
            existing_count = connection.execute('SELECT COUNT(*) FROM users').fetchone()[0]
            cursor = connection.execute(
                '''INSERT INTO users
                   (username, password_salt, password_hash, password_iterations, created_at)
                   VALUES (?, ?, ?, ?, ?)''',
                (
                    username, salt, password_hash, self.PBKDF2_ITERATIONS,
                    datetime.now(timezone.utc).isoformat(timespec='seconds'),
                ),
            )
            user_id = cursor.lastrowid
            if existing_count == 0:
                # Assign pre-account history to the first registered user.
                connection.execute(
                    'UPDATE bmi_history SET user_id = ? WHERE user_id IS NULL', (user_id,)
                )
            return user_id

    def authenticate(self, username, password):
        with closing(sqlite3.connect(self.history_db)) as connection, connection:
            row = connection.execute(
                '''SELECT id, username, password_salt, password_hash, password_iterations
                   FROM users WHERE username = ?''',
                (username,),
            ).fetchone()

        if not row:
            return None
        user_id, stored_username, salt, stored_hash, iterations = row
        if not 1_000 <= iterations <= 2_000_000:
            return None
        candidate = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
        if hmac.compare_digest(stored_hash, candidate):
            return user_id, stored_username
        return None

    def set_auto_login(self, user_id):
        with closing(sqlite3.connect(self.history_db)) as connection, connection:
            if user_id is None:
                connection.execute(
                    "DELETE FROM app_settings WHERE setting_key = 'auto_login_user_id'"
                )
            else:
                connection.execute(
                    '''INSERT INTO app_settings (setting_key, setting_value)
                       VALUES ('auto_login_user_id', ?)
                       ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value''',
                    (str(user_id),),
                )

    def get_auto_login_user(self):
        with closing(sqlite3.connect(self.history_db)) as connection, connection:
            row = connection.execute(
                '''SELECT users.id, users.username
                   FROM app_settings
                   JOIN users ON users.id = CAST(app_settings.setting_value AS INTEGER)
                   WHERE app_settings.setting_key = 'auto_login_user_id' '''
            ).fetchone()
            if row:
                return row[0], row[1]
            connection.execute(
                "DELETE FROM app_settings WHERE setting_key = 'auto_login_user_id'"
            )
        return None

    def load_latest_height(self, user_id):
        with closing(sqlite3.connect(self.history_db)) as connection, connection:
            row = connection.execute(
                '''SELECT height_cm FROM bmi_history
                   WHERE user_id = ?
                   ORDER BY datetime(measured_at) DESC, id DESC LIMIT 1''',
                (user_id,),
            ).fetchone()
            return row[0] if row else None

    def save_history(self, user_id, measured_date, height, weight, bmi):
        with closing(sqlite3.connect(self.history_db)) as connection, connection:
            connection.execute(
                '''INSERT INTO bmi_history
                   (user_id, measured_at, height_cm, weight_kg, bmi)
                   VALUES (?, ?, ?, ?, ?)''',
                (user_id, measured_date, height, weight, bmi),
            )

    def load_history(self, user_id):
        with closing(sqlite3.connect(self.history_db)) as connection:
            return connection.execute(
                '''SELECT measured_at, bmi, height_cm, weight_kg FROM bmi_history
                   WHERE user_id = ? ORDER BY datetime(measured_at), id''',
                (user_id,),
            ).fetchall()

    def load_editable_history(self, user_id):
        with closing(sqlite3.connect(self.history_db)) as connection:
            return connection.execute(
                '''SELECT id, measured_at, height_cm, weight_kg, bmi
                   FROM bmi_history WHERE user_id = ?
                   ORDER BY datetime(measured_at) DESC, id DESC''',
                (user_id,),
            ).fetchall()

    def update_history_record(self, user_id, record_id, measured_date, height, weight):
        bmi = weight / (height / 100) ** 2
        with closing(sqlite3.connect(self.history_db)) as connection, connection:
            cursor = connection.execute(
                '''UPDATE bmi_history
                   SET measured_at = ?, height_cm = ?, weight_kg = ?, bmi = ?
                   WHERE id = ? AND user_id = ?''',
                (measured_date, height, weight, bmi, record_id, user_id),
            )
            return cursor.rowcount == 1

    def clear_widgets(self):
        for child in self.winfo_children():
            child.destroy()

    @staticmethod
    def make_button(parent, text, command, primary=False, **options):
        background = COLORS['primary'] if primary else '#e8eef6'
        foreground = COLORS['white'] if primary else COLORS['navy']
        active_background = COLORS['primary_active'] if primary else '#dbe4f0'
        return tk.Button(
            parent, text=text, command=command, bg=background, fg=foreground,
            activebackground=active_background, activeforeground=foreground,
            relief='flat', borderwidth=0, padx=16, pady=10, cursor='hand2',
            font=('Yu Gothic UI', 10, 'bold'), **options,
        )

    def show_auth_screen(self):
        self.clear_widgets()
        self.configure(background=COLORS['background'], menu='')
        self.title('BMI計算機 | アカウント')
        self.geometry('540x620')
        self.resizable(False, False)

        with closing(sqlite3.connect(self.history_db)) as connection:
            user_count = connection.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        self.auth_mode = 'register' if user_count == 0 else 'login'

        page = tk.Frame(self, bg=COLORS['background'])
        page.pack(fill='both', expand=True)
        card = tk.Frame(
            page, bg=COLORS['white'], padx=36, pady=32,
            highlightthickness=1, highlightbackground=COLORS['border'],
        )
        card.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(
            card, text='BMI', bg=COLORS['primary'], fg=COLORS['white'],
            font=('Yu Gothic UI', 12, 'bold'), padx=12, pady=6,
        ).pack(anchor='center', pady=(0, 12))
        tk.Label(
            card, text='BMI計算機', bg=COLORS['white'], fg=COLORS['navy'],
            font=('Yu Gothic UI', 20, 'bold'),
        ).pack()
        tk.Label(
            card, text='アカウントで測定履歴を管理', bg=COLORS['white'],
            fg=COLORS['muted'], font=FONT,
        ).pack(pady=(4, 20))

        mode_bar = tk.Frame(card, bg=COLORS['background'], padx=4, pady=4)
        mode_bar.pack(fill='x', pady=(0, 18))
        self.mode_buttons = {}
        for mode, label in (('login', 'ログイン'), ('register', '新規登録')):
            button = tk.Button(
                mode_bar, text=label, command=lambda selected=mode: self.set_auth_mode(selected),
                relief='flat', borderwidth=0, padx=16, pady=8, cursor='hand2', font=FONT,
            )
            button.pack(side='left', fill='x', expand=True)
            self.mode_buttons[mode] = button

        self.auth_form = tk.Frame(card, bg=COLORS['white'])
        self.auth_form.pack(fill='x')
        self.set_auth_mode(self.auth_mode)

        tk.Label(
            card, text='アカウントと履歴はこのPCのアプリデータ内に保存されます。',
            bg=COLORS['white'], fg=COLORS['muted'], font=('Yu Gothic UI', 8),
            wraplength=410,
        ).pack(pady=(18, 0))

    def set_auth_mode(self, mode):
        self.auth_mode = mode
        for name, button in self.mode_buttons.items():
            selected = name == mode
            button.configure(
                bg=COLORS['white'] if selected else COLORS['background'],
                fg=COLORS['navy'] if selected else COLORS['muted'],
                font=('Yu Gothic UI', 10, 'bold' if selected else 'normal'),
            )
        self.render_auth_form()

    def render_auth_form(self):
        for child in self.auth_form.winfo_children():
            child.destroy()

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()
        self.remember_var = tk.BooleanVar(value=False)
        self.auth_error_var = tk.StringVar(value='')

        tk.Label(self.auth_form, text='ユーザー名', bg=COLORS['white'], fg=COLORS['text'], font=FONT).pack(anchor='w')
        self.username_entry = tk.Entry(
            self.auth_form, textvariable=self.username_var, font=FONT, relief='flat',
            highlightthickness=1, highlightbackground=COLORS['border'],
            highlightcolor=COLORS['primary'],
        )
        self.username_entry.pack(fill='x', ipady=8, pady=(5, 13))

        tk.Label(self.auth_form, text='パスワード', bg=COLORS['white'], fg=COLORS['text'], font=FONT).pack(anchor='w')
        self.password_entry = tk.Entry(
            self.auth_form, textvariable=self.password_var, show='*', font=FONT, relief='flat',
            highlightthickness=1, highlightbackground=COLORS['border'],
            highlightcolor=COLORS['primary'],
        )
        self.password_entry.pack(fill='x', ipady=8, pady=(5, 13))

        if self.auth_mode == 'register':
            tk.Label(
                self.auth_form, text='パスワード（確認）', bg=COLORS['white'],
                fg=COLORS['text'], font=FONT,
            ).pack(anchor='w')
            self.confirm_entry = tk.Entry(
                self.auth_form, textvariable=self.confirm_password_var, show='*',
                font=FONT, relief='flat', highlightthickness=1,
                highlightbackground=COLORS['border'], highlightcolor=COLORS['primary'],
            )
            self.confirm_entry.pack(fill='x', ipady=8, pady=(5, 10))
            self.confirm_entry.bind('<Return>', lambda _event: self.submit_auth())

        tk.Checkbutton(
            self.auth_form, text='次回から自動ログイン', variable=self.remember_var,
            bg=COLORS['white'], activebackground=COLORS['white'], fg=COLORS['text'],
            selectcolor=COLORS['white'], font=FONT,
        ).pack(anchor='w', pady=(0, 8))
        tk.Label(
            self.auth_form, textvariable=self.auth_error_var, bg=COLORS['white'],
            fg=COLORS['error'], font=FONT, justify='left', wraplength=400,
        ).pack(anchor='w', pady=(0, 8))

        action_label = 'アカウントを作成' if self.auth_mode == 'register' else 'ログイン'
        self.make_button(
            self.auth_form, action_label, self.submit_auth, primary=True,
        ).pack(fill='x')
        self.username_entry.bind('<Return>', lambda _event: self.password_entry.focus_set())
        self.password_entry.bind(
            '<Return>', lambda _event: self.confirm_entry.focus_set()
            if self.auth_mode == 'register' else self.submit_auth(),
        )
        self.username_entry.focus_set()

    def submit_auth(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username or len(username) > 32 or any(ord(char) < 32 or ord(char) == 127 for char in username):
            self.auth_error_var.set('ユーザー名を1〜32文字で入力してください。')
            return
        if len(password) < 8 or len(password) > 128:
            self.auth_error_var.set('パスワードは8〜128文字で入力してください。')
            return

        if self.auth_mode == 'register':
            if password != self.confirm_password_var.get():
                self.auth_error_var.set('確認用パスワードが一致しません。')
                return
            try:
                user_id = self.create_account(username, password)
            except sqlite3.IntegrityError:
                self.auth_error_var.set('そのユーザー名はすでに登録されています。')
                return
            except sqlite3.Error as error:
                messagebox.showerror('登録エラー', f'アカウントを作成できませんでした。\n{error}', parent=self)
                return
            account = (user_id, username)
        else:
            try:
                account = self.authenticate(username, password)
            except sqlite3.Error as error:
                messagebox.showerror('ログインエラー', f'ログインできませんでした。\n{error}', parent=self)
                return
            if account is None:
                self.auth_error_var.set('ユーザー名またはパスワードが正しくありません。')
                return

        try:
            self.set_auto_login(account[0] if self.remember_var.get() else None)
        except sqlite3.Error as error:
            messagebox.showwarning(
                '設定エラー', f'自動ログイン設定を保存できませんでした。\n{error}', parent=self,
            )
        self.open_main(*account)

    def open_main(self, user_id, username):
        self.user_id = user_id
        self.username = username
        try:
            self.seed_sample_history(user_id)
        except (OSError, sqlite3.Error) as error:
            messagebox.showwarning('履歴データ', f'初期履歴を準備できませんでした。\n{error}', parent=self)
        self.default_height = self.load_latest_height(user_id)
        self.create_widgets()

    def logout(self):
        try:
            self.set_auto_login(None)
        except sqlite3.Error:
            pass
        self.user_id = None
        self.username = None
        self.show_auth_screen()

    def create_widgets(self):
        self.clear_widgets()
        self.configure(background=COLORS['background'])
        self.title('BMI計算機')
        self.geometry('1260x760')
        self.resizable(False, False)
        menu_bar = tk.Menu(self)
        data_menu = tk.Menu(menu_bar, tearoff=False)
        data_menu.add_command(label='過去のデータを編集…', command=self.open_history_editor)
        menu_bar.add_cascade(label='データ', menu=data_menu)
        self.configure(menu=menu_bar)

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

        content = tk.Frame(self, bg=COLORS['background'], padx=22, pady=20)
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
        self.height_field, self.height_entry = self.create_input_field(card, '身長', 'cm', self.height_var)
        self.height_field.pack(fill='x', pady=(0, 14))
        self.weight_field, self.weight_entry = self.create_input_field(card, '体重', 'kg', self.weight_var)
        self.weight_field.pack(fill='x')
        self.weight_entry.bind('<Return>', lambda _event: self.bmi_cal())

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

        self.make_button(card, '計算して保存', self.bmi_cal, primary=True).pack(fill='x')
        tk.Label(
            card, text='計算結果は履歴グラフへ自動で反映されます。', bg=COLORS['white'],
            fg=COLORS['muted'], font=('Yu Gothic UI', 9),
            wraplength=260, justify='left',
        ).pack(anchor='w', pady=(14, 0))
        self.height_entry.focus_set()

        graph_card = tk.Frame(
            content, bg=COLORS['white'], padx=18, pady=18,
            highlightthickness=1, highlightbackground=COLORS['border'],
        )
        graph_card.grid(row=0, column=1, sticky='nsew')
        tk.Label(
            graph_card, text='BMIの推移', bg=COLORS['white'], fg=COLORS['navy'],
            font=('Yu Gothic UI', 15, 'bold'),
        ).pack(anchor='w')
        tk.Label(
            graph_card, text='過去の測定履歴', bg=COLORS['white'],
            fg=COLORS['muted'], font=('Yu Gothic UI', 9),
        ).pack(anchor='w', pady=(2, 12))

        graph_body = tk.Frame(graph_card, bg=COLORS['white'])
        graph_body.pack(fill='both', expand=True)
        chart_stack = tk.Frame(graph_body, bg=COLORS['white'])
        chart_stack.pack(side='left', fill='both', expand=True)

        bmi_panel = tk.Frame(chart_stack, bg=COLORS['white'])
        bmi_panel.pack(fill='both', expand=True, pady=(0, 6))
        tk.Label(
            bmi_panel, text='BMI', bg=COLORS['white'], fg=COLORS['muted'],
            font=('Yu Gothic UI', 9, 'bold'),
        ).pack(anchor='w')
        self.history_canvas = tk.Canvas(
            bmi_panel, background=COLORS['white'], highlightthickness=0,
        )
        self.history_canvas.pack(fill='both', expand=True)

        measurement_panel = tk.Frame(chart_stack, bg=COLORS['white'])
        measurement_panel.pack(fill='both', expand=True, pady=(6, 0))
        tk.Label(
            measurement_panel, text='身長（左・cm）／体重（右・kg）',
            bg=COLORS['white'], fg=COLORS['muted'],
            font=('Yu Gothic UI', 9, 'bold'),
        ).pack(anchor='w')
        self.measurement_canvas = tk.Canvas(
            measurement_panel, background=COLORS['white'], highlightthickness=0,
        )
        self.measurement_canvas.pack(fill='both', expand=True)

        legend = tk.Frame(graph_body, padx=12, pady=12, width=390, bg=COLORS['white'])
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
        self.history_records = []
        self.history_canvas.bind('<Configure>', self.draw_bmi_graph)
        self.measurement_canvas.bind('<Configure>', self.draw_measurement_graph)
        self.refresh_history_graph()

    @staticmethod
    def create_input_field(parent, label, unit, variable):
        field = tk.Frame(parent, bg=COLORS['white'])
        tk.Label(
            field, text=label, bg=COLORS['white'], fg=COLORS['text'], font=FONT,
        ).pack(anchor='w', pady=(0, 6))
        row = tk.Frame(field, bg=COLORS['white'])
        row.pack(fill='x')
        entry = tk.Entry(
            row, textvariable=variable, font=('Yu Gothic UI', 12), justify='center',
            relief='flat', highlightthickness=1, highlightbackground=COLORS['border'],
            highlightcolor=COLORS['primary'],
        )
        entry.pack(side='left', fill='x', expand=True, ipady=8)
        if unit:
            tk.Label(
                row, text=unit, bg=COLORS['white'], fg=COLORS['muted'], font=FONT,
            ).pack(side='left', padx=(8, 0))
        return field, entry

    def bmi_cal(self):
        try:
            measured_date = self.date_picker.get_date().isoformat()
            height = float(self.height_var.get())
            weight = float(self.weight_var.get())
            if not math.isfinite(height) or not math.isfinite(weight) or height <= 0 or weight <= 0:
                raise ValueError('Measurements must be positive finite numbers')
            bmi = weight / (height / 100) ** 2
            if not math.isfinite(bmi):
                raise ValueError('BMI is not finite')
        except (ValueError, ZeroDivisionError, OverflowError, tk.TclError):
            self.bmi_result.set('入力エラー')
            self.judge.set('日付・身長・体重を正しく入力してください')
            return

        self.bmi_result.set(f'{bmi:.3f}')
        if bmi < 16.0:
            category = JUDGE_LIST[0]
        elif bmi < 17.0:
            category = JUDGE_LIST[1]
        elif bmi < 18.5:
            category = JUDGE_LIST[2]
        elif bmi < 25.0:
            category = JUDGE_LIST[3]
        elif bmi < 30.0:
            category = JUDGE_LIST[4]
        elif bmi < 35.0:
            category = JUDGE_LIST[5]
        elif bmi < 40.0:
            category = JUDGE_LIST[6]
        else:
            category = JUDGE_LIST[7]
        self.judge.set(category)

        try:
            self.save_history(self.user_id, measured_date, height, weight, bmi)
        except (OSError, sqlite3.Error) as error:
            messagebox.showerror(
                '保存エラー', f'計算結果を履歴に保存できませんでした。\n{error}', parent=self,
            )
            return
        self.refresh_history_graph()

    def refresh_history_graph(self):
        try:
            records = self.load_history(self.user_id)
        except (OSError, sqlite3.Error) as error:
            messagebox.showerror('読み込みエラー', f'履歴を読み込めませんでした。\n{error}', parent=self)
            self.history_records = []
            self.draw_bmi_graph()
            self.draw_measurement_graph()
            return
        self.history_records = records
        self.draw_bmi_graph()
        self.draw_measurement_graph()

    @staticmethod
    def display_measurement_date(value):
        measured_at = datetime.fromisoformat(value)
        if measured_at.tzinfo is not None:
            measured_at = measured_at.astimezone()
        return measured_at.date().isoformat()

    def open_history_editor(self):
        window = tk.Toplevel(self)
        window.title('過去のデータを編集')
        window.geometry('800x540')
        window.resizable(False, False)
        window.configure(background=COLORS['background'])

        card = tk.Frame(
            window, bg=COLORS['white'], padx=20, pady=18,
            highlightthickness=1, highlightbackground=COLORS['border'],
        )
        card.pack(fill='both', expand=True, padx=18, pady=18)
        tk.Label(
            card, text='過去の測定データ', bg=COLORS['white'], fg=COLORS['navy'],
            font=('Yu Gothic UI', 14, 'bold'),
        ).pack(anchor='w')
        tk.Label(
            card, text='編集する行を選択するか、行をダブルクリックしてください。',
            bg=COLORS['white'], fg=COLORS['muted'], font=FONT,
        ).pack(anchor='w', pady=(3, 12))

        table_frame = tk.Frame(card, bg=COLORS['white'])
        table_frame.pack(fill='both', expand=True)
        columns = ('date', 'height', 'weight', 'bmi')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=14)
        tree.heading('date', text='測定日')
        tree.heading('height', text='身長（cm）')
        tree.heading('weight', text='体重（kg）')
        tree.heading('bmi', text='BMI')
        tree.column('date', width=180, anchor='center')
        tree.column('height', width=150, anchor='center')
        tree.column('weight', width=150, anchor='center')
        tree.column('bmi', width=150, anchor='center')
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        style = ttk.Style(window)
        style.configure('Treeview', rowheight=28, font=FONT)
        style.configure('Treeview.Heading', font=('Yu Gothic UI', 9, 'bold'))
        self.populate_history_tree(tree, window)
        tree.bind('<Double-1>', lambda _event: self.edit_selected_history(tree, window))

        actions = tk.Frame(card, bg=COLORS['white'])
        actions.pack(fill='x', pady=(14, 0))
        self.make_button(
            actions, '選択したデータを編集',
            lambda: self.edit_selected_history(tree, window), primary=True,
        ).pack(side='left')
        self.make_button(actions, '閉じる', window.destroy).pack(side='right')

    def populate_history_tree(self, tree, parent):
        try:
            records = self.load_editable_history(self.user_id)
        except sqlite3.Error as error:
            messagebox.showerror('履歴エラー', f'履歴を読み込めませんでした。\n{error}', parent=parent)
            return

        for item in tree.get_children():
            tree.delete(item)
        for record_id, measured_at, height, weight, bmi in records:
            tree.insert(
                '', 'end', iid=str(record_id),
                values=(self.display_measurement_date(measured_at), f'{height:g}', f'{weight:g}', f'{bmi:.3f}'),
            )

    def edit_selected_history(self, tree, parent):
        selection = tree.selection()
        if not selection:
            messagebox.showinfo('データ編集', '編集するデータを選択してください。', parent=parent)
            return

        record_id = int(selection[0])
        measured_date, height, weight, _bmi = tree.item(selection[0], 'values')
        dialog = tk.Toplevel(parent)
        dialog.title('測定データを編集')
        dialog.geometry('460x450')
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.grab_set()
        dialog.configure(background=COLORS['background'])

        card = tk.Frame(
            dialog, bg=COLORS['white'], padx=28, pady=24,
            highlightthickness=1, highlightbackground=COLORS['border'],
        )
        card.pack(fill='both', expand=True, padx=16, pady=16)
        tk.Label(
            card, text='測定データを編集', bg=COLORS['white'], fg=COLORS['navy'],
            font=('Yu Gothic UI', 14, 'bold'),
        ).pack(anchor='w', pady=(0, 16))

        date_picker = DatePicker(card, '測定日', date.fromisoformat(measured_date))
        height_var = tk.StringVar(value=height)
        weight_var = tk.StringVar(value=weight)
        date_picker.pack(fill='x', pady=(0, 12))
        for label, unit, variable in (('身長', 'cm', height_var), ('体重', 'kg', weight_var)):
            field, _entry = self.create_input_field(card, label, unit, variable)
            field.pack(fill='x', pady=(0, 12))

        actions = tk.Frame(card, bg=COLORS['white'])
        actions.pack(fill='x', pady=(8, 0))
        self.make_button(actions, '保存', lambda: self.save_history_edit(
            record_id, date_picker, height_var, weight_var, dialog, tree, parent,
        ), primary=True).pack(side='left', fill='x', expand=True, padx=(0, 6))
        self.make_button(actions, 'キャンセル', dialog.destroy).pack(
            side='left', fill='x', expand=True, padx=(6, 0),
        )

    def save_history_edit(self, record_id, date_picker, height_var, weight_var, dialog, tree, parent):
        try:
            measured_date = date_picker.get_date().isoformat()
            height = float(height_var.get())
            weight = float(weight_var.get())
            if not math.isfinite(height) or not math.isfinite(weight) or height <= 0 or weight <= 0:
                raise ValueError('Measurements must be positive finite numbers')
            bmi = weight / (height / 100) ** 2
            if not math.isfinite(bmi):
                raise ValueError('BMI is not finite')
        except (ValueError, ZeroDivisionError, OverflowError):
            messagebox.showerror(
                '入力エラー', '日付・身長・体重を正しく入力してください。', parent=dialog,
            )
            return

        previous_default = self.default_height
        try:
            updated = self.update_history_record(
                self.user_id, record_id, measured_date, height, weight,
            )
        except sqlite3.Error as error:
            messagebox.showerror('保存エラー', f'データを更新できませんでした。\n{error}', parent=dialog)
            return
        if not updated:
            messagebox.showerror('保存エラー', '選択したデータが見つかりません。', parent=dialog)
            return

        current_height = self.height_var.get().strip()
        self.default_height = self.load_latest_height(self.user_id)
        if previous_default is not None and current_height == f'{previous_default:g}':
            self.height_var.set(
                '' if self.default_height is None else f'{self.default_height:g}'
            )
        dialog.destroy()
        self.populate_history_tree(tree, parent)
        self.refresh_history_graph()

    def draw_bmi_graph(self, _event=None):
        canvas = self.history_canvas
        canvas.delete('all')
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width < 140 or height < 100:
            return
        if not self.history_records:
            canvas.create_text(
                width / 2, height / 2, text='測定履歴がありません',
                fill=COLORS['muted'], font=('Yu Gothic UI', 11),
            )
            return

        left, right, top, bottom = 52, width - 12, 12, height - 38
        if right <= left or bottom <= top:
            return
        values = [record[1] for record in self.history_records]
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

        count = len(self.history_records)
        points = []
        for index, record in enumerate(self.history_records):
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

        label_count = min(count, 4)
        label_indices = sorted({
            round(index * (count - 1) / max(label_count - 1, 1))
            for index in range(label_count)
        })
        for index in label_indices:
            x = left + (right - left) * index / max(count - 1, 1)
            measured_at = datetime.fromisoformat(self.history_records[index][0]).astimezone()
            canvas.create_text(
                x, bottom + 12, text=measured_at.strftime('%Y/%m'),
                anchor='n', fill=COLORS['muted'], font=('Yu Gothic UI', 9),
            )

    def draw_measurement_graph(self, _event=None):
        canvas = self.measurement_canvas
        canvas.delete('all')
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width < 150 or height < 100:
            return
        if not self.history_records:
            canvas.create_text(
                width / 2, height / 2, text='測定履歴がありません',
                fill=COLORS['muted'], font=('Yu Gothic UI', 10),
            )
            return

        left, right, top, bottom = 48, width - 48, 12, height - 38
        if right <= left or bottom <= top:
            return

        heights = [record[2] for record in self.history_records]
        weights = [record[3] for record in self.history_records]

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

        count = len(self.history_records)
        height_points = []
        weight_points = []
        for index, record in enumerate(self.history_records):
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

        label_count = min(count, 4)
        label_indices = sorted({
            round(index * (count - 1) / max(label_count - 1, 1))
            for index in range(label_count)
        })
        for index in label_indices:
            x = left + (right - left) * index / max(count - 1, 1)
            measured_at = datetime.fromisoformat(self.history_records[index][0]).astimezone()
            canvas.create_text(
                x, bottom + 11, text=measured_at.strftime('%Y/%m'),
                anchor='n', fill=COLORS['muted'], font=('Yu Gothic UI', 8),
            )


def main():
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
