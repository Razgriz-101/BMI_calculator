"""Integration tests for SQLite authentication and measurement history."""

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from storage import Storage


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.original_iterations = Storage.PBKDF2_ITERATIONS
        Storage.PBKDF2_ITERATIONS = 1_000
        self.temp_dir = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.database_path = Path(self.temp_dir.name) / 'test_history.sqlite3'
        self.storage = Storage(self.database_path)

    def tearDown(self):
        Storage.PBKDF2_ITERATIONS = self.original_iterations
        self.temp_dir.cleanup()

    def test_new_database_starts_without_sample_history(self):
        self.assertEqual(self.storage.load_history(1), [])
        with closing(self.storage.connect()) as connection:
            count = connection.execute('SELECT COUNT(*) FROM bmi_history').fetchone()[0]
        self.assertEqual(count, 0)

    def test_account_authentication_and_auto_login_setting(self):
        user_id = self.storage.create_account('alice', 'safe-password-1')
        self.assertEqual(
            self.storage.authenticate('alice', 'safe-password-1'),
            (user_id, 'alice'),
        )
        self.assertIsNone(self.storage.authenticate('alice', 'incorrect-password'))

        self.storage.set_auto_login(user_id)
        self.assertEqual(self.storage.get_auto_login_user(), (user_id, 'alice'))
        self.storage.set_auto_login(None)
        self.assertIsNone(self.storage.get_auto_login_user())

    def test_duplicate_usernames_are_rejected_case_insensitively(self):
        self.storage.create_account('Alice', 'safe-password-1')
        with self.assertRaises(sqlite3.IntegrityError):
            self.storage.create_account('alice', 'safe-password-2')

    def test_history_is_scoped_updated_and_deleted_by_owner(self):
        first_user = self.storage.create_account('first', 'safe-password-1')
        second_user = self.storage.create_account('second', 'safe-password-2')
        self.storage.save_history(first_user, '2026-03-10', 170.0, 65.0, 65 / 1.7 ** 2)
        self.storage.save_history(second_user, '2026-03-11', 180.0, 80.0, 80 / 1.8 ** 2)

        first_records = self.storage.load_history(first_user)
        self.assertEqual(len(first_records), 1)
        self.assertEqual(first_records[0][0], '2026-03-10')
        record_id = self.storage.load_editable_history(first_user)[0][0]
        self.assertEqual(self.storage.load_latest_height(first_user), 170.0)

        self.assertFalse(self.storage.delete_history_record(second_user, record_id))
        self.assertTrue(
            self.storage.update_history_record(
                first_user, record_id, '2026-03-12', 175.0, 70.0,
            )
        )
        updated = self.storage.load_history(first_user)[0]
        self.assertEqual(updated[0], '2026-03-12')
        self.assertAlmostEqual(updated[1], 70 / 1.75 ** 2)
        self.assertEqual(updated[2], 175.0)
        self.assertTrue(self.storage.delete_history_record(first_user, record_id))
        self.assertEqual(self.storage.load_history(first_user), [])
        self.assertEqual(len(self.storage.load_history(second_user)), 1)

    def test_legacy_history_is_migrated_to_first_registered_user(self):
        legacy_path = Path(self.temp_dir.name) / 'legacy.sqlite3'
        with closing(sqlite3.connect(legacy_path)) as connection, connection:
            connection.execute(
                '''CREATE TABLE bmi_history (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       measured_at TEXT NOT NULL,
                       height_cm REAL NOT NULL,
                       weight_kg REAL NOT NULL,
                       bmi REAL NOT NULL,
                       is_sample INTEGER NOT NULL DEFAULT 0
                   )'''
            )
            connection.execute(
                '''INSERT INTO bmi_history
                   (measured_at, height_cm, weight_kg, bmi)
                   VALUES (?, ?, ?, ?)''',
                ('2024-05-01', 168.0, 60.0, 60 / 1.68 ** 2),
            )

        migrated = Storage(legacy_path)
        user_id = migrated.create_account('legacy-user', 'safe-password-3')
        records = migrated.load_history(user_id)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0][0], '2024-05-01')
        with closing(migrated.connect()) as connection:
            row = connection.execute(
                'SELECT user_id, is_sample FROM bmi_history'
            ).fetchone()
        self.assertEqual(row, (user_id, 0))


if __name__ == '__main__':
    unittest.main()
