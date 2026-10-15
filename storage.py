"""ユーザー、設定、測定履歴のSQLite保存を管理します。"""

import hashlib
import hmac
import os
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from bmi_logic import calculate_bmi


class Storage:
    """SQLiteデータベースへの認証・履歴アクセスを提供します。"""

    PBKDF2_ITERATIONS = 600_000

    def __init__(self, database_path=None):
        self.database_path = Path(database_path) if database_path else self.default_database_path()
        self.initialize_database()

    @staticmethod
    def default_database_path():
        """現在のOSユーザー用データベースの保存先を返します。"""
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

    def connect(self):
        return sqlite3.connect(self.database_path)

    def initialize_database(self):
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as connection, connection:
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

    def user_count(self):
        with closing(self.connect()) as connection:
            return connection.execute('SELECT COUNT(*) FROM users').fetchone()[0]

    @staticmethod
    def hash_password(password, salt):
        return hashlib.pbkdf2_hmac(
            'sha256', password.encode('utf-8'), salt, Storage.PBKDF2_ITERATIONS,
        )

    def create_account(self, username, password):
        salt = secrets.token_bytes(16)
        password_hash = self.hash_password(password, salt)
        with closing(self.connect()) as connection, connection:
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
                connection.execute(
                    'UPDATE bmi_history SET user_id = ? WHERE user_id IS NULL', (user_id,)
                )
            return user_id

    def authenticate(self, username, password):
        with closing(self.connect()) as connection:
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
        with closing(self.connect()) as connection, connection:
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
        with closing(self.connect()) as connection, connection:
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
        with closing(self.connect()) as connection:
            row = connection.execute(
                '''SELECT height_cm FROM bmi_history
                   WHERE user_id = ?
                   ORDER BY datetime(measured_at) DESC, id DESC LIMIT 1''',
                (user_id,),
            ).fetchone()
            return row[0] if row else None

    def save_history(self, user_id, measured_date, height, weight, bmi):
        with closing(self.connect()) as connection, connection:
            connection.execute(
                '''INSERT INTO bmi_history
                   (user_id, measured_at, height_cm, weight_kg, bmi)
                   VALUES (?, ?, ?, ?, ?)''',
                (user_id, measured_date, height, weight, bmi),
            )

    def load_history(self, user_id):
        with closing(self.connect()) as connection:
            return connection.execute(
                '''SELECT measured_at, bmi, height_cm, weight_kg FROM bmi_history
                   WHERE user_id = ? ORDER BY datetime(measured_at), id''',
                (user_id,),
            ).fetchall()

    def load_editable_history(self, user_id):
        with closing(self.connect()) as connection:
            return connection.execute(
                '''SELECT id, measured_at, height_cm, weight_kg, bmi
                   FROM bmi_history WHERE user_id = ?
                   ORDER BY datetime(measured_at) DESC, id DESC''',
                (user_id,),
            ).fetchall()

    def update_history_record(self, user_id, record_id, measured_date, height, weight):
        bmi, _category = calculate_bmi(height, weight)
        with closing(self.connect()) as connection, connection:
            cursor = connection.execute(
                '''UPDATE bmi_history
                   SET measured_at = ?, height_cm = ?, weight_kg = ?, bmi = ?
                   WHERE id = ? AND user_id = ?''',
                (measured_date, height, weight, bmi, record_id, user_id),
            )
            return cursor.rowcount == 1

    def delete_history_record(self, user_id, record_id):
        """指定ユーザーが所有する測定履歴を1件削除します。"""
        with closing(self.connect()) as connection, connection:
            cursor = connection.execute(
                'DELETE FROM bmi_history WHERE id = ? AND user_id = ?',
                (record_id, user_id),
            )
            return cursor.rowcount == 1

    @staticmethod
    def display_measurement_date(value):
        measured_at = datetime.fromisoformat(value)
        if measured_at.tzinfo is not None:
            measured_at = measured_at.astimezone()
        return measured_at.date().isoformat()
