from sqlite3 import Connection
from typing import Generator

from catalog import AnimalCatalog, StaffNotificationCatalog
from db import initialize_db
from fastapi import Depends


def get_db() -> Generator[Connection, None, None]:
    yield from initialize_db()


def get_animal_catalog(conn: Connection = Depends(get_db)) -> AnimalCatalog:
    return AnimalCatalog(conn)


def get_staff_notification_catalog(
    conn: Connection = Depends(get_db),
) -> StaffNotificationCatalog:
    return StaffNotificationCatalog(conn)
