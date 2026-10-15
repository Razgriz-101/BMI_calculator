"""GUI interaction tests for the main BMI application screens."""

import tkinter as tk
import unittest
from datetime import date, timedelta

from app import App
from bmi_logic import calculate_bmi


class InMemoryStorage:
    """Small storage double that keeps GUI tests isolated from user data."""

    def __init__(self):
        today = date.today()
        recent_date = today.isoformat()
        older_date = (today - timedelta(days=60)).isoformat()
        recent_bmi, _category = calculate_bmi(171.0, 65.0)
        older_bmi, _category = calculate_bmi(170.0, 68.0)
        self.records = [
            (1, recent_date, 171.0, 65.0, recent_bmi),
            (2, older_date, 170.0, 68.0, older_bmi),
        ]
        self.next_record_id = 3
        self.auto_login_user = None

    def get_auto_login_user(self):
        return self.auto_login_user

    @staticmethod
    def user_count():
        """Report one account so the auth form can initialize in login mode."""
        return 1

    def set_auto_login(self, user_id):
        self.auto_login_user = user_id

    def load_latest_height(self, user_id):
        if not self.records:
            return None
        latest = max(self.records, key=lambda record: (record[1], record[0]))
        return latest[2]

    def load_history(self, user_id):
        return [
            (measured_at, bmi, height, weight)
            for _record_id, measured_at, height, weight, bmi in sorted(
                self.records, key=lambda record: (record[1], record[0]),
            )
        ]

    def load_editable_history(self, user_id):
        return sorted(self.records, key=lambda record: (record[1], record[0]), reverse=True)

    @staticmethod
    def display_measurement_date(value):
        return date.fromisoformat(value).isoformat()

    def save_history(self, user_id, measured_date, height, weight, bmi):
        self.records.append((self.next_record_id, measured_date, height, weight, bmi))
        self.next_record_id += 1

    def update_history_record(self, user_id, record_id, measured_date, height, weight):
        for index, record in enumerate(self.records):
            if record[0] == record_id:
                bmi, _category = calculate_bmi(height, weight)
                self.records[index] = (record_id, measured_date, height, weight, bmi)
                return True
        return False

    def delete_history_record(self, user_id, record_id):
        remaining = [record for record in self.records if record[0] != record_id]
        if len(remaining) == len(self.records):
            return False
        self.records = remaining
        return True


class GuiTests(unittest.TestCase):
    """Exercise navigation and measurement flows when a Tk display is available."""

    def setUp(self):
        try:
            display_probe = tk.Tk()
            display_probe.withdraw()
            display_probe.destroy()
        except tk.TclError as error:
            self.skipTest(f'Tk display is unavailable: {error}')

        self.storage = InMemoryStorage()
        self.app = App(storage=self.storage)
        self.app.withdraw()
        self.app.open_main(1, 'gui-test-user')
        self.app.update_idletasks()

    def tearDown(self):
        app = getattr(self, 'app', None)
        if app is not None:
            try:
                app.destroy()
            except tk.TclError:
                pass

    def test_tab_navigation_and_edit_form_stay_in_main_window(self):
        self.app.show_main_page('history')
        editor = self.app.pages['history']
        self.assertEqual(self.app.current_page_name, 'history')
        self.assertIs(editor.winfo_toplevel(), self.app)

        first_record_id = editor.tree.get_children()[0]
        editor.tree.selection_set(first_record_id)
        editor.edit_selected()

        self.assertIs(editor.winfo_toplevel(), self.app)
        self.assertIs(self.app.pages['history'], editor)
        self.assertEqual(self.app.current_page_name, 'history')

    def test_measurement_input_saves_and_refreshes_graph(self):
        self.assertEqual(self.app.height_var.get(), '171')
        self.app.weight_var.set('70')

        self.app.calculate_and_save()

        expected_bmi, _category = calculate_bmi(171.0, 70.0)
        self.assertAlmostEqual(float(self.app.bmi_result.get()), expected_bmi, places=3)
        self.assertTrue(any(record[3] == 70.0 for record in self.storage.records))
        self.assertTrue(any(record[3] == 70.0 for record in self.app.graph_panel.all_records))

    def test_history_and_graph_period_controls_filter_their_records(self):
        editor = self.app.pages['history']
        editor.period_var.set('1週間')
        editor.apply_filter()
        visible_history_ids = set(editor.tree.get_children())
        self.assertIn('1', visible_history_ids)
        self.assertNotIn('2', visible_history_ids)

        graph_records = [
            (measured_at, bmi, height, weight)
            for _record_id, measured_at, height, weight, bmi in self.storage.records
        ]
        self.app.graph_panel.set_records(graph_records)
        self.app.graph_panel.period_var.set('1週間')
        self.app.graph_panel.apply_period()
        self.assertEqual(len(self.app.graph_panel.records), 1)
        self.assertEqual(self.app.graph_panel.records[0][0], date.today().isoformat())

    def test_custom_period_controls_keep_the_main_window_size(self):
        initial_size = self.app.geometry().split('+')[0]
        editor = self.app.pages['history']
        editor.period_var.set('自由設定')
        editor.on_period_changed()
        self.app.graph_panel.period_var.set('自由設定')
        self.app.graph_panel.on_period_changed()
        self.app.update_idletasks()

        self.assertEqual(editor.custom_controls.winfo_manager(), 'pack')
        self.assertEqual(self.app.graph_panel.custom_controls.winfo_manager(), 'pack')
        self.assertEqual(self.app.geometry().split('+')[0], initial_size)

    def test_history_delete_confirmation_removes_record_inline(self):
        self.app.show_main_page('history')
        editor = self.app.pages['history']
        editor.tree.selection_set('1')

        editor.request_delete()
        self.assertEqual(editor.pending_delete_id, 1)
        self.assertEqual(editor.confirm_panel.winfo_manager(), 'pack')
        editor.confirm_delete()

        self.assertFalse(any(record[0] == 1 for record in self.storage.records))
        self.assertIs(editor.winfo_toplevel(), self.app)
        self.assertNotIn('1', editor.tree.get_children())


if __name__ == '__main__':
    unittest.main()
