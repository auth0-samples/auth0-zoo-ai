import logging
import sqlite3
from contextlib import closing
from pathlib import Path
from sqlite3 import Connection
from typing import Generator

logger = logging.getLogger(__name__)


def initialize_db() -> Generator[Connection, None, None]:
    logger.info("Starting database")

    Path("./data").mkdir(exist_ok=True)

    conn = sqlite3.connect("data/db", check_same_thread=False)

    if __create_schema(conn):
        __load_start_data(conn)

    try:
        yield conn
    finally:
        conn.close()


def __create_schema(conn: Connection) -> bool:
    """returns true if the schema needed to be created and false if the schema already existed"""

    with closing(conn.cursor()) as cursor:
        cursor.execute(
            """
            SELECT 1 FROM sqlite_master WHERE type='table' and name='animal'
        """
        )

        result = cursor.fetchone()

        if result:
            return False

        ## creates the db schema
        cursor.execute(
            """
        CREATE TABLE animal (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                specie TEXT NOT NULL,
                age INTEGER NOT NULL
            );
        """
        )
        cursor.execute(
            """
            CREATE TABLE animal_status (
                animal_id TEXT NOT NULL,
                time DATETIME NOT NULL,
                status TEXT NOT NULL,
                user_role TEXT NOT NULL CHECK (user_role IN ('JANITOR', 'VETERINARIAN', 'COORDINATOR', 'ZOOKEEPER')),
                user_id TEXT NOT NULL,
                PRIMARY KEY (animal_id, time),
                FOREIGN KEY (animal_id) REFERENCES animal(id) ON DELETE CASCADE
            );
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS staff_notification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time DATETIME NOT NULL,
                description TEXT NOT NULL,
                destination_role TEXT NOT NULL CHECK (destination_role IN ('JANITOR', 'VETERINARIAN', 'COORDINATOR', 'ZOOKEEPER')),
                notifier_role TEXT NOT NULL CHECK (notifier_role IN ('JANITOR', 'VETERINARIAN', 'COORDINATOR', 'ZOOKEEPER')),
                notifier_id TEXT NOT NULL
            );
        """
        )

    __load_start_data(conn)

    return True


def __load_start_data(conn: Connection):
    logger.info("DB does not exist. Loading start data")
    with closing(conn.cursor()) as cursor:
        sql = """
            INSERT INTO animal(id, name, specie, age) VALUES (?,?,?,?)
        """
        animals = [
            ("ALEX", "Alex", "Lion", 4),
            ("KING_JULIEN", "King Julien", "Lemur", 12),
            ("MORT", "Mort", "Mouse lemur", 50),
            ("SKIPPER", "Skipper", "Penguin", 35),
            ("MARTY", "Marty", "Zebra", 10),
            ("GLORIA", "Gloria", "Hippopotamus", 6),
            ("PRIVATE", "Private", "Penguin", 10),
            ("KOWALSKI", "Kowalski", "Penguin", 3),
        ]
        cursor.executemany(sql, animals)
        conn.commit()
