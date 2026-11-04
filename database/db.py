import logging
import os
import sqlite3
from datetime import date

from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

# Database lives in the project root (already git-ignored as expense_tracker.db).
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "expense_tracker.db",
)

CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
]


def get_db():
    """Open a SQLite connection with dict-like rows and FK enforcement.

    Logs and re-raises sqlite3.Error if the database cannot be opened or
    configured.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error:
        logger.exception("Could not open database at %s", DB_PATH)
        if conn is not None:
            conn.close()
        raise


def init_db():
    """Create all tables if they don't exist. Safe to call repeatedly."""
    conn = get_db()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                email         TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at    TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                amount      REAL NOT NULL,
                category    TEXT NOT NULL,
                date        TEXT NOT NULL,
                description TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        logger.exception("init_db failed while creating tables")
        raise
    finally:
        conn.close()


def seed_db():
    """Insert a demo user and sample expenses, only if no users exist."""
    conn = get_db()
    try:
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
            return

        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
        )
        user_id = cur.lastrowid

        today = date.today()
        samples = [
            (450.50, "Food", 2, "Groceries"),
            (120.00, "Transport", 4, "Metro card recharge"),
            (1800.00, "Bills", 6, "Electricity bill"),
            (650.75, "Health", 9, "Pharmacy"),
            (399.00, "Entertainment", 13, "Movie night"),
            (2200.00, "Shopping", 17, "New shoes"),
            (150.00, "Other", 21, "Miscellaneous"),
            (320.25, "Food", 25, "Dinner out"),
        ]
        rows = [
            (user_id, amount, category, today.replace(day=day).isoformat(), desc)
            for amount, category, day, desc in samples
        ]
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    except sqlite3.Error:
        # Roll back so a failed seed never leaves a user without expenses
        # (which would make the next seed_db() skip as "already seeded").
        conn.rollback()
        logger.exception("seed_db failed; transaction rolled back")
        raise
    finally:
        conn.close()
