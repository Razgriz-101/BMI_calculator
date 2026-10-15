"""メイン画面内で測定履歴を一覧、編集、削除します。"""

import tkinter as tk
from datetime import date
from tkinter import ttk

from bmi_logic import calculate_bmi
from date_picker import DatePicker
from date_ranges import PERIOD_OPTIONS, filter_records_by_date, period_range
from ui_style import COLORS, FONT, create_input_field, make_button


class HistoryEditor(tk.Frame):
    """ログインユーザーの過去データを表示するページです。"""

    def __init__(self, parent, storage, user_id, on_updated):
        super().__init__(parent, bg=COLORS['background'])
        self.storage = storage
        self.user_id = user_id
        self.on_updated = on_updated
        self.period_var = tk.StringVar(value='すべて')
        self.custom_start, self.custom_end = period_range('1年')
        self.show_list()

    def _clear(self):
        for child in self.winfo_children():
            child.destroy()

    def show_list(self):
        self._clear()
        card = tk.Frame(
            self, bg=COLORS['white'], padx=24, pady=22,
            highlightthickness=1, highlightbackground=COLORS['border'],
        )
        card.pack(fill='both', expand=True, padx=22, pady=20)

        filter_bar = tk.Frame(card, bg=COLORS['white'])
        filter_bar.pack(fill='x', pady=(0, 8))
        filter_controls = tk.Frame(filter_bar, bg=COLORS['white'], height=64)
        filter_controls.pack(fill='x')
        filter_controls.pack_propagate(False)
        tk.Label(
            filter_controls, text='表示期間', bg=COLORS['white'], fg=COLORS['text'],
            font=('Yu Gothic UI', 9, 'bold'),
        ).pack(side='left', padx=(0, 8))
        self.period_box = ttk.Combobox(
            filter_controls, textvariable=self.period_var,
            values=('すべて', *PERIOD_OPTIONS, '自由設定'),
            state='readonly', width=10,
        )
        self.period_box.pack(side='left')

        self.custom_controls = tk.Frame(filter_controls, bg=COLORS['white'])
        self.start_picker = DatePicker(self.custom_controls, '開始日', self.custom_start)
        self.start_picker.pack(side='left', padx=(10, 4))
        self.end_picker = DatePicker(self.custom_controls, '終了日', self.custom_end)
        self.end_picker.pack(side='left', padx=4)
        tk.Button(
            self.custom_controls, text='適用', command=self.apply_filter,
            bg='#e8eef6', fg=COLORS['navy'], activebackground='#dbe4f0',
            relief='flat', borderwidth=0, padx=12, pady=8, cursor='hand2',
            font=('Yu Gothic UI', 9, 'bold'),
        ).pack(side='left', padx=(4, 0), pady=(20, 0))
        if self.period_var.get() == '自由設定':
            self.custom_controls.pack(side='left', padx=(10, 0))
        self.period_box.bind('<<ComboboxSelected>>', self.on_period_changed)
        self.filter_status_var = tk.StringVar(value='')

        self.status_var = tk.StringVar(value='')
        tk.Label(
            card, textvariable=self.status_var, bg=COLORS['white'],
            fg=COLORS['error'], font=FONT, anchor='w',
        ).pack(fill='x', pady=(0, 6))

        actions = tk.Frame(card, bg=COLORS['white'])
        actions.pack(fill='x', pady=(0, 12))
        make_button(actions, '選択したデータを編集', self.edit_selected, primary=True).pack(side='left')
        tk.Button(
            actions, text='選択したデータを削除', command=self.request_delete,
            bg='#fee2e2', fg='#b42318', activebackground='#fecaca',
            activeforeground='#991b1b', relief='flat', borderwidth=0,
            padx=12, pady=10, cursor='hand2', font=('Yu Gothic UI', 10, 'bold'),
        ).pack(side='left', padx=(8, 0))
        tk.Label(
            actions, textvariable=self.filter_status_var, bg=COLORS['white'],
            fg=COLORS['muted'], font=('Yu Gothic UI', 8), anchor='e', justify='right',
        ).pack(side='right', fill='x', expand=True, padx=(12, 0))

        self.confirm_panel = tk.Frame(card, bg='#fff7ed', padx=12, pady=8)
        self.confirm_text = tk.Label(
            self.confirm_panel, bg='#fff7ed', fg=COLORS['text'], font=FONT,
        )
        self.confirm_text.pack(side='left', fill='x', expand=True)
        tk.Button(
            self.confirm_panel, text='削除する', command=self.confirm_delete,
            bg='#b42318', fg=COLORS['white'], activebackground='#991b1b',
            activeforeground=COLORS['white'], relief='flat', borderwidth=0,
            padx=12, pady=8, cursor='hand2', font=('Yu Gothic UI', 9, 'bold'),
        ).pack(side='left', padx=(8, 0))
        make_button(
            self.confirm_panel, 'キャンセル', self.cancel_delete,
        ).pack(side='left', padx=(8, 0))

        table_frame = tk.Frame(card, bg=COLORS['white'])
        table_frame.pack(fill='both', expand=True)
        columns = ('date', 'height', 'weight', 'bmi')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=14)
        self.tree.heading('date', text='測定日')
        self.tree.heading('height', text='身長（cm）')
        self.tree.heading('weight', text='体重（kg）')
        self.tree.heading('bmi', text='BMI')
        self.tree.column('date', width=220, anchor='center')
        self.tree.column('height', width=200, anchor='center')
        self.tree.column('weight', width=200, anchor='center')
        self.tree.column('bmi', width=200, anchor='center')
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        style = ttk.Style(self)
        style.configure('Treeview', rowheight=30, font=FONT)
        style.configure('Treeview.Heading', font=('Yu Gothic UI', 9, 'bold'))
        self.refresh()
        self.tree.bind('<Double-1>', lambda _event: self.edit_selected())

    def refresh(self):
        try:
            self.all_records = self.storage.load_editable_history(self.user_id)
        except Exception as error:
            self.status_var.set(f'履歴を読み込めませんでした: {error}')
            return
        self.apply_filter()

    def on_period_changed(self, _event=None):
        if self.period_var.get() == '自由設定':
            self.custom_controls.pack(side='left', padx=(10, 0))
        else:
            self.custom_controls.pack_forget()
        self.apply_filter()

    def apply_filter(self):
        period = self.period_var.get()
        self.status_var.set('')
        if period == 'すべて':
            records = self.all_records
            self.filter_status_var.set(f'全期間の履歴: {len(records)}件')
        elif period == '自由設定':
            start = self.start_picker.get_date()
            end = self.end_picker.get_date()
            self.custom_start, self.custom_end = start, end
            if start > end:
                self.status_var.set('開始日は終了日以前の日付にしてください。')
                self.filter_status_var.set('')
                self._populate_tree([])
                return
            records = filter_records_by_date(
                self.all_records, start, end, date_index=1,
            )
            self.filter_status_var.set(f'{start:%Y-%m-%d} ～ {end:%Y-%m-%d}　／　{len(records)}件')
        else:
            start, end = period_range(period)
            records = filter_records_by_date(
                self.all_records, start, end, date_index=1,
            )
            self.filter_status_var.set(f'{start:%Y-%m-%d} ～ {end:%Y-%m-%d}　／　{len(records)}件')

        self._populate_tree(records)

    def _populate_tree(self, records):
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

    def _selected_row(self):
        selection = self.tree.selection()
        if not selection:
            self.status_var.set('先に履歴を選択してください。')
            return None
        return selection[0], self.tree.item(selection[0], 'values')

    def request_delete(self):
        selected = self._selected_row()
        if selected is None:
            return
        item_id, values = selected
        self.confirm_text.configure(
            text=f'{values[0]} の測定データを削除しますか？削除後は元に戻せません。'
        )
        self.confirm_panel.pack(fill='x', before=self.tree.master, pady=(0, 10))
        self.pending_delete_id = int(item_id)
        self.status_var.set('')

    def cancel_delete(self):
        self.confirm_panel.pack_forget()
        self.pending_delete_id = None

    def confirm_delete(self):
        record_id = getattr(self, 'pending_delete_id', None)
        if record_id is None:
            return
        try:
            previous_default = self.storage.load_latest_height(self.user_id)
            deleted = self.storage.delete_history_record(self.user_id, record_id)
        except Exception as error:
            self.status_var.set(f'データを削除できませんでした: {error}')
            self.cancel_delete()
            return
        if not deleted:
            self.status_var.set('選択したデータが見つかりません。')
            self.cancel_delete()
            return
        self.on_updated(previous_default)
        self.show_list()

    def edit_selected(self):
        selected = self._selected_row()
        if selected is None:
            return
        item_id, values = selected
        self.show_edit_form(int(item_id), values)

    def show_edit_form(self, record_id, values):
        self._clear()
        card = tk.Frame(
            self, bg=COLORS['white'], padx=30, pady=26, width=540,
            highlightthickness=1, highlightbackground=COLORS['border'],
        )
        card.pack(anchor='nw', padx=22, pady=20)
        tk.Label(
            card, text='測定データを編集', bg=COLORS['white'], fg=COLORS['navy'],
            font=('Yu Gothic UI', 15, 'bold'),
        ).pack(anchor='w', pady=(0, 18))

        date_picker = DatePicker(card, '測定日', values[0])
        height_var = tk.StringVar(value=values[1])
        weight_var = tk.StringVar(value=values[2])
        date_picker.pack(fill='x', pady=(0, 12))
        for label, unit, variable in (('身長', 'cm', height_var), ('体重', 'kg', weight_var)):
            field, _entry = create_input_field(card, label, unit, variable)
            field.pack(fill='x', pady=(0, 12))

        self.status_var = tk.StringVar(value='')
        tk.Label(
            card, textvariable=self.status_var, bg=COLORS['white'],
            fg=COLORS['error'], font=FONT, anchor='w',
        ).pack(fill='x', pady=(0, 8))
        actions = tk.Frame(card, bg=COLORS['white'])
        actions.pack(fill='x')
        make_button(
            actions, '保存', lambda: self.save_edit(
                record_id, date_picker, height_var, weight_var,
            ), primary=True,
        ).pack(side='left', fill='x', expand=True, padx=(0, 6))
        make_button(actions, 'キャンセル', self.show_list).pack(
            side='left', fill='x', expand=True, padx=(6, 0),
        )

    def save_edit(self, record_id, date_picker, height_var, weight_var):
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
            self.status_var.set('日付・身長・体重を正しく入力してください。')
            return
        except Exception as error:
            self.status_var.set(f'データを保存できませんでした: {error}')
            return
        if not updated:
            self.status_var.set('選択したデータが見つかりません。')
            return
        self.on_updated(previous_default)
        self.show_list()
