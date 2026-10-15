"""ローカルユーザーの登録とログイン画面を提供します。"""

import sqlite3
import tkinter as tk
from tkinter import messagebox

from ui_style import COLORS, FONT, make_button


class AuthScreen(tk.Frame):
    """Local account registration and sign-in screen."""

    def __init__(self, parent, storage, on_authenticated):
        super().__init__(parent, bg=COLORS['background'])
        self.storage = storage
        self.on_authenticated = on_authenticated
        self.auth_mode = 'register' if storage.user_count() == 0 else 'login'
        self.pack(fill='both', expand=True)
        self._build()

    def _build(self):
        card = tk.Frame(
            self, bg=COLORS['white'], padx=36, pady=32,
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
        self._render_auth_form()

    def _render_auth_form(self):
        for child in self.auth_form.winfo_children():
            child.destroy()

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()
        self.remember_var = tk.BooleanVar(value=False)
        self.auth_error_var = tk.StringVar(value='')

        tk.Label(
            self.auth_form, text='ユーザー名', bg=COLORS['white'],
            fg=COLORS['text'], font=FONT,
        ).pack(anchor='w')
        self.username_entry = tk.Entry(
            self.auth_form, textvariable=self.username_var, font=FONT, relief='flat',
            highlightthickness=1, highlightbackground=COLORS['border'],
            highlightcolor=COLORS['primary'],
        )
        self.username_entry.pack(fill='x', ipady=8, pady=(5, 13))

        tk.Label(
            self.auth_form, text='パスワード', bg=COLORS['white'],
            fg=COLORS['text'], font=FONT,
        ).pack(anchor='w')
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
            self.confirm_entry.bind('<Return>', lambda _event: self.submit())

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
        make_button(self.auth_form, action_label, self.submit, primary=True).pack(fill='x')
        self.username_entry.bind('<Return>', lambda _event: self.password_entry.focus_set())
        self.password_entry.bind(
            '<Return>', lambda _event: self.confirm_entry.focus_set()
            if self.auth_mode == 'register' else self.submit(),
        )
        self.username_entry.focus_set()

    def submit(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        if not username or len(username) > 32 or any(
            ord(char) < 32 or ord(char) == 127 for char in username
        ):
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
                account = (self.storage.create_account(username, password), username)
            except sqlite3.IntegrityError:
                self.auth_error_var.set('そのユーザー名はすでに登録されています。')
                return
            except sqlite3.Error as error:
                messagebox.showerror('登録エラー', f'アカウントを作成できませんでした。\n{error}', parent=self)
                return
        else:
            try:
                account = self.storage.authenticate(username, password)
            except sqlite3.Error as error:
                messagebox.showerror('ログインエラー', f'ログインできませんでした。\n{error}', parent=self)
                return
            if account is None:
                self.auth_error_var.set('ユーザー名またはパスワードが正しくありません。')
                return

        try:
            self.storage.set_auto_login(account[0] if self.remember_var.get() else None)
        except sqlite3.Error as error:
            messagebox.showwarning(
                '設定エラー', f'自動ログイン設定を保存できませんでした。\n{error}', parent=self,
            )
        self.on_authenticated(*account)
