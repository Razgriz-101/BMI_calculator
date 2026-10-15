"""共通配色とTkinterのボタン・入力欄を定義します。"""

import tkinter as tk


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


def make_button(parent, text, command, primary=False, **options):
    """共通配色と余白を使ったボタンを生成します。"""
    background = COLORS['primary'] if primary else '#e8eef6'
    foreground = COLORS['white'] if primary else COLORS['navy']
    active_background = COLORS['primary_active'] if primary else '#dbe4f0'
    return tk.Button(
        parent, text=text, command=command, bg=background, fg=foreground,
        activebackground=active_background, activeforeground=foreground,
        relief='flat', borderwidth=0, padx=16, pady=10, cursor='hand2',
        font=('Yu Gothic UI', 10, 'bold'), **options,
    )


def create_input_field(parent, label, unit, variable):
    """ラベル、入力欄、単位をまとめた入力フィールドを生成します。"""
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
