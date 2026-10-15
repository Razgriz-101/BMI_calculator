"""ログインユーザーの過去の測定履歴を一覧表示して編集します。"""

import tkinter as tk
from tkinter import messagebox, ttk

from bmi_logic import calculate_bmi
from date_picker import DatePicker
from ui_style import COLORS, FONT, create_input_field, make_button


class HistoryEditor(tk.Toplevel):
    """List and edit the signed-in user's measurements."""

    def __init__(self, parent, storage, user_id, on_updated):
        super().__init__(parent)
        self.storage = storage
        self.user_id = user_id
        self.on_updated = on_updated
        self.title('過去のデータを編集')
        self.geometry('800x540')
        self.resizable(False, False)
        self.configure(background=COLORS['background'])
        self._build()

    def _build(self):
        card = tk.Frame(
            self, bg=COLORS['white'], padx=20, pady=18,
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
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=14)
        self.tree.heading('date', text='測定日')
        self.tree.heading('height', text='身長（cm）')
        self.tree.heading('weight', text='体重（kg）')
        self.tree.heading('bmi', text='BMI')
        self.tree.column('date', width=180, anchor='center')
        self.tree.column('height', width=150, anchor='center')
        self.tree.column('weight', width=150, anchor='center')
        self.tree.column('bmi', width=150, anchor='center')
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        style = ttk.Style(self)
        style.configure('Treeview', rowheight=28, font=FONT)
        style.configure('Treeview.Heading', font=('Yu Gothic UI', 9, 'bold'))
        self.refresh()
        self.tree.bind('<Double-1>', lambda _event: self.edit_selected())

        actions = tk.Frame(card, bg=COLORS['white'])
        actions.pack(fill='x', pady=(14, 0))
        make_button(actions, '選択したデータを編集', self.edit_selected, primary=True).pack(side='left')
        make_button(actions, '閉じる', self.destroy).pack(side='right')

    def refresh(self):
        try:
            records = self.storage.load_editable_history(self.user_id)
        except Exception as error:
            messagebox.showerror('履歴エラー', f'履歴を読み込めませんでした。\n{error}', parent=self)
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        for record_id, measured_at, height, weight, bmi in records:
            self.tree.insert(
                '', 'end', iid=str(record_id),
                values=(
                    self.storage.display_measurement_date(measured_at),
                    f'{height:g}', f'{weight:g}', f'{bmi:.3f}',
                ),
            )

    def edit_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo('データ編集', '編集するデータを選択してください。', parent=self)
            return

        record_id = int(selection[0])
        measured_date, height, weight, _bmi = self.tree.item(selection[0], 'values')
        dialog = tk.Toplevel(self)
        dialog.title('測定データを編集')
        dialog.geometry('460x450')
        dialog.resizable(False, False)
        dialog.transient(self)
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

        date_picker = DatePicker(card, '測定日', measured_date)
        height_var = tk.StringVar(value=height)
        weight_var = tk.StringVar(value=weight)
        date_picker.pack(fill='x', pady=(0, 12))
        for label, unit, variable in (('身長', 'cm', height_var), ('体重', 'kg', weight_var)):
            field, _entry = create_input_field(card, label, unit, variable)
            field.pack(fill='x', pady=(0, 12))

        actions = tk.Frame(card, bg=COLORS['white'])
        actions.pack(fill='x', pady=(8, 0))
        make_button(
            actions, '保存', lambda: self.save_edit(
                record_id, date_picker, height_var, weight_var, dialog,
            ), primary=True,
        ).pack(side='left', fill='x', expand=True, padx=(0, 6))
        make_button(actions, 'キャンセル', dialog.destroy).pack(
            side='left', fill='x', expand=True, padx=(6, 0),
        )

    def save_edit(self, record_id, date_picker, height_var, weight_var, dialog):
        try:
            measured_date = date_picker.get_date().isoformat()
            height = float(height_var.get())
            weight = float(weight_var.get())
            calculate_bmi(height, weight)
            previous_default = self.storage.load_latest_height(self.user_id)
            updated = self.storage.update_history_record(
                self.user_id, record_id, measured_date, height, weight,
            )
        except (ValueError, ZeroDivisionError, OverflowError):
            messagebox.showerror(
                '入力エラー', '日付・身長・体重を正しく入力してください。', parent=dialog,
            )
            return
        except Exception as error:
            messagebox.showerror('保存エラー', f'データを更新できませんでした。\n{error}', parent=dialog)
            return

        if not updated:
            messagebox.showerror('保存エラー', '選択したデータが見つかりません。', parent=dialog)
            return
        dialog.destroy()
        self.refresh()
        self.on_updated(previous_default)
