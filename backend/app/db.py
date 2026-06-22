import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from app.schemas import BoardData

DEFAULT_COLUMNS = [
    {"id": "col-backlog", "title": "Backlog", "position": 0},
    {"id": "col-discovery", "title": "Discovery", "position": 1},
    {"id": "col-progress", "title": "In Progress", "position": 2},
    {"id": "col-review", "title": "Review", "position": 3},
    {"id": "col-done", "title": "Done", "position": 4},
]

DEFAULT_CARDS = [
    {
        "id": "card-1",
        "title": "Align roadmap themes",
        "details": "Draft quarterly themes with impact statements and metrics.",
        "column_id": "col-backlog",
        "position": 0,
    },
    {
        "id": "card-2",
        "title": "Gather customer signals",
        "details": "Review support tags, sales notes, and churn feedback.",
        "column_id": "col-backlog",
        "position": 1,
    },
    {
        "id": "card-3",
        "title": "Prototype analytics view",
        "details": "Sketch initial dashboard layout and key drill-downs.",
        "column_id": "col-discovery",
        "position": 0,
    },
    {
        "id": "card-4",
        "title": "Refine status language",
        "details": "Standardize column labels and tone across the board.",
        "column_id": "col-progress",
        "position": 0,
    },
    {
        "id": "card-5",
        "title": "Design card layout",
        "details": "Add hierarchy and spacing for scanning dense lists.",
        "column_id": "col-progress",
        "position": 1,
    },
    {
        "id": "card-6",
        "title": "QA micro-interactions",
        "details": "Verify hover, focus, and loading states.",
        "column_id": "col-review",
        "position": 0,
    },
    {
        "id": "card-7",
        "title": "Ship marketing page",
        "details": "Final copy approved and asset pack delivered.",
        "column_id": "col-done",
        "position": 0,
    },
    {
        "id": "card-8",
        "title": "Close onboarding sprint",
        "details": "Document release notes and share internally.",
        "column_id": "col-done",
        "position": 1,
    },
]


def get_db_path() -> Path:
    override = os.environ.get("PM_DB_PATH")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent.parent / "data" / "pm.db"


@contextmanager
def db_connection() -> Iterable[sqlite3.Connection]:
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS boards (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        CREATE TABLE IF NOT EXISTS columns (
            id TEXT PRIMARY KEY,
            board_id TEXT NOT NULL,
            title TEXT NOT NULL,
            position INTEGER NOT NULL,
            FOREIGN KEY (board_id) REFERENCES boards (id)
        );
        CREATE TABLE IF NOT EXISTS cards (
            id TEXT PRIMARY KEY,
            board_id TEXT NOT NULL,
            column_id TEXT NOT NULL,
            title TEXT NOT NULL,
            details TEXT NOT NULL,
            position INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (board_id) REFERENCES boards (id),
            FOREIGN KEY (column_id) REFERENCES columns (id)
        );
        """
    )


def ensure_user_and_board(conn: sqlite3.Connection, username: str) -> str:
    init_db(conn)
    user = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if user:
        user_id = user["id"]
    else:
        user_id = f"user-{username}"
        conn.execute(
            "INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (user_id, username, "", utc_now()),
        )

    board = conn.execute(
        "SELECT id FROM boards WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if board:
        return board["id"]

    board_id = f"board-{username}"
    conn.execute(
        "INSERT INTO boards (id, user_id, title, created_at) VALUES (?, ?, ?, ?)",
        (board_id, user_id, "Default Board", utc_now()),
    )
    for column in DEFAULT_COLUMNS:
        conn.execute(
            "INSERT INTO columns (id, board_id, title, position) VALUES (?, ?, ?, ?)",
            (column["id"], board_id, column["title"], column["position"]),
        )
    for card in DEFAULT_CARDS:
        now = utc_now()
        conn.execute(
            """
            INSERT INTO cards (id, board_id, column_id, title, details, position, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                card["id"],
                board_id,
                card["column_id"],
                card["title"],
                card["details"],
                card["position"],
                now,
                now,
            ),
        )
    return board_id


def read_board(conn: sqlite3.Connection, username: str) -> BoardData:
    board_id = ensure_user_and_board(conn, username)

    columns_rows = conn.execute(
        "SELECT id, title, position FROM columns WHERE board_id = ? ORDER BY position",
        (board_id,),
    ).fetchall()
    cards_rows = conn.execute(
        """
        SELECT id, title, details, column_id, position
        FROM cards
        WHERE board_id = ?
        ORDER BY position
        """,
        (board_id,),
    ).fetchall()

    card_ids_by_column: dict[str, list[str]] = {row["id"]: [] for row in columns_rows}
    cards: dict[str, dict[str, str]] = {}

    for row in cards_rows:
        cards[row["id"]] = {
            "id": row["id"],
            "title": row["title"],
            "details": row["details"],
        }
        card_ids_by_column.setdefault(row["column_id"], []).append(row["id"])

    columns = [
        {
            "id": row["id"],
            "title": row["title"],
            "cardIds": card_ids_by_column.get(row["id"], []),
        }
        for row in columns_rows
    ]

    return BoardData(columns=columns, cards=cards)


def validate_board(board: BoardData) -> None:
    column_ids = [column.id for column in board.columns]
    if len(column_ids) != len(set(column_ids)):
        raise ValueError("Duplicate column ids are not allowed.")

    card_ids = list(board.cards.keys())
    if len(card_ids) != len(set(card_ids)):
        raise ValueError("Duplicate card ids are not allowed.")

    referenced_card_ids: list[str] = []
    for column in board.columns:
        for card_id in column.cardIds:
            if card_id not in board.cards:
                raise ValueError(f"Card id {card_id} not found in cards map.")
            if card_id in referenced_card_ids:
                raise ValueError(f"Card id {card_id} is referenced more than once.")
            referenced_card_ids.append(card_id)

    missing = set(board.cards.keys()) - set(referenced_card_ids)
    if missing:
        raise ValueError("All cards must be referenced by a column.")


def write_board(conn: sqlite3.Connection, username: str, board: BoardData) -> BoardData:
    validate_board(board)
    board_id = ensure_user_and_board(conn, username)
    now = utc_now()

    conn.execute("DELETE FROM cards WHERE board_id = ?", (board_id,))
    conn.execute("DELETE FROM columns WHERE board_id = ?", (board_id,))

    for position, column in enumerate(board.columns):
        conn.execute(
            "INSERT INTO columns (id, board_id, title, position) VALUES (?, ?, ?, ?)",
            (column.id, board_id, column.title, position),
        )

    for column in board.columns:
        for position, card_id in enumerate(column.cardIds):
            card = board.cards[card_id]
            conn.execute(
                """
                INSERT INTO cards (id, board_id, column_id, title, details, position, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    card.id,
                    board_id,
                    column.id,
                    card.title,
                    card.details,
                    position,
                    now,
                    now,
                ),
            )

    return read_board(conn, username)
