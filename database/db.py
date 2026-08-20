import os
import sqlite3
from werkzeug.security import generate_password_hash

# Database file lives at the project root, alongside app.py.
DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "spendly.db")
)


def get_db() -> sqlite3.Connection:
    """Open a SQLite connection to spendly.db.

    Returns a connection with dict-style row access (``sqlite3.Row``) and
    foreign-key enforcement enabled via ``PRAGMA foreign_keys = ON``.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create the ``users`` and ``expenses`` tables if they do not exist.

    Safe to call repeatedly: ``CREATE TABLE IF NOT EXISTS`` makes the
    operation idempotent. Schema and constraints come from the project spec
    at ``.claude/specs/01-database-setup.md``.
    """
    conn = get_db()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                email         TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at    TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                amount      REAL    NOT NULL,
                category    TEXT    NOT NULL,
                date        TEXT    NOT NULL,
                description TEXT,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def seed_db() -> None:
    """Insert the demo user and 8 sample expenses, exactly once.

    If the ``users`` table already contains any rows, this function returns
    without making changes. Otherwise it inserts the demo user
    (``demo@spendly.com`` / ``demo123``) and 8 expenses for August 2026 that
    cover every fixed category from the spec.
    """
    conn = get_db()
    try:
        existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if existing > 0:
            return

        cursor = conn.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (
                "Demo User",
                "demo@spendly.com",
                generate_password_hash("demo123"),
            ),
        )
        demo_user_id = cursor.lastrowid

        sample_expenses = [
            ("2026-08-01", "Bills",         89.50, "Internet bill"),
            ("2026-08-03", "Food",          12.75, "Lunch at cafe"),
            ("2026-08-05", "Transport",      4.20, "Metro fare"),
            ("2026-08-08", "Health",        32.00, "Pharmacy"),
            ("2026-08-11", "Entertainment", 14.99, "Streaming subscription"),
            ("2026-08-14", "Shopping",      56.40, "Groceries"),
            ("2026-08-17", "Food",          28.30, "Dinner with friends"),
            ("2026-08-19", "Transport",     22.50, "Rideshare to airport"),
        ]

        conn.executemany(
            """
            INSERT INTO expenses (user_id, date, category, amount, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (demo_user_id, date, category, amount, description)
                for date, category, amount, description in sample_expenses
            ],
        )

        conn.commit()
    finally:
        conn.close()
