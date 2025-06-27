import logging
from pathlib import Path
from typing import Generator
from tinydb import TinyDB
from schema import Animal

logger = logging.getLogger(__name__)

def initialize_db() -> Generator[TinyDB]:
    logger.info("Starting database")
    Path("./data").mkdir(exist_ok=True)
    db_path = "./data/db.json"
    file_exists = Path(db_path).exists()
    db = TinyDB(db_path)
    if not file_exists:
        __load_start_data(db)
    try:
        yield db
    finally:
        db.close()


def __load_start_data(db: TinyDB):
    logger.info("DB does not exist. Loading start data")
    zoo_animals = [
        Animal(id="ALEX", name="Alex", specie="Lion", age=4, last_status=[]),
        Animal(
            id="KING_JULIEN", name="King Julien", specie="Lemur", age=12, last_status=[]
        ),
        Animal(id="MORT", name="Mort", specie="Mouse lemur", age=50, last_status=[]),
        Animal(id="SKIPPER", name="Skipper", specie="Penguin", age=35, last_status=[]),
        Animal(id="MARTY", name="Marty", specie="Zebra", age=10, last_status=[]),
        Animal(
            id="GLORIA", name="Gloria", specie="Hippopotamus", age=6, last_status=[]
        ),
        Animal(id="PRIVATE", name="Private", specie="Penguin", age=10, last_status=[]),
        Animal(id="KOWALSKI", name="Kowalski", specie="Lion", age=3, last_status=[]),
    ]
    db.table("animals").insert_multiple([animal.model_dump() for animal in zoo_animals])
