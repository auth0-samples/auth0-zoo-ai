from typing import Generator
from fastapi import Depends
from tinydb import TinyDB
from db import initialize_db
from catalog import AnimalCatalog, StaffNotificationCatalog

def get_db() -> Generator[TinyDB]:
    yield from initialize_db()

def get_animal_catalog(db: TinyDB = Depends(get_db)) -> AnimalCatalog:
    return AnimalCatalog(db)

def get_staff_notification_catalog(db: TinyDB = Depends(get_db)) -> StaffNotificationCatalog:
    return StaffNotificationCatalog(db)
