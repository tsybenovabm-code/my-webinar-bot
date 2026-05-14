import sqlite3
from datetime import datetime


class Database:
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    chat_id     INTEGER PRIMARY KEY,
                    username    TEXT,
                    full_name   TEXT,
                    joined_at   TEXT
                )
            """)
            conn.commit()

    def add_user(self, chat_id: int, username: str, full_name: str) -> bool:
        """Добавляет пользователя. Возвращает True если новый, False если уже есть."""
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT 1 FROM users WHERE chat_id = ?", (chat_id,)
            ).fetchone()

            if existing:
                return False

            conn.execute(
                "INSERT INTO users (chat_id, username, full_name, joined_at) VALUES (?, ?, ?, ?)",
                (chat_id, username, full_name, datetime.now().isoformat()),
            )
            conn.commit()
            return True

    def get_all_users(self) -> list:
        with self._connect() as conn:
            return conn.execute("SELECT chat_id FROM users").fetchall()

    def get_user_count(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
