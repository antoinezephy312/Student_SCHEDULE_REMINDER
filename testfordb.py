import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("schedule.db")

DEFAULT_USERS = {
    "student": {"password": "1234", "fullname": "Student User", "role": "student"},
    "admin": {"password": "admin123", "fullname": "Administrator", "role": "admin"},
    "instructor": {"password": "teach123", "fullname": "Instructor", "role": "instructor"},
}


def ensure_table_columns(cursor, table_name, columns):
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing = {row[1] for row in cursor.fetchall()}
    for column_name, definition in columns.items():
        if column_name not in existing:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {definition}")


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                fullname TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student'
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                subject TEXT NOT NULL,
                section TEXT NOT NULL,
                course TEXT NOT NULL,
                year_level TEXT NOT NULL,
                instructor TEXT NOT NULL,
                term TEXT NOT NULL,
                deadline TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """
        )

        ensure_table_columns(cursor, "users", {"role": "role TEXT NOT NULL DEFAULT 'student'"})
        ensure_table_columns(cursor, "tasks", {
            "section": "section TEXT NOT NULL DEFAULT ''",
            "course": "course TEXT NOT NULL DEFAULT ''",
            "year_level": "year_level TEXT NOT NULL DEFAULT ''",
            "instructor": "instructor TEXT NOT NULL DEFAULT ''",
            "term": "term TEXT NOT NULL DEFAULT 'Prelim'",
        })

        for username, info in DEFAULT_USERS.items():
            cursor.execute(
                """
                INSERT OR IGNORE INTO users (username, password, fullname, role)
                VALUES (?, ?, ?, ?)
                """,
                (username, info["password"], info["fullname"], info["role"])
            )
            cursor.execute(
                "UPDATE users SET role = ? WHERE username = ?",
                (info["role"], username)
            )
        conn.commit()


def dump_table(table_name):
    if table_name not in {"users", "tasks"}:
        raise ValueError("Unsupported table requested.")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

    if not rows:
        print(f"No rows found in {table_name}.")
        return

    for row in rows:
        print(row)


if __name__ == "__main__":
    init_db()
    print("Users:")
    dump_table("users")
    print("\nTasks:")
    dump_table("tasks")
