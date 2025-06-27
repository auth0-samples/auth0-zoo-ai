import enum
from datetime import datetime

from pydantic import BaseModel


class UpdateAnimalStatusRequest(BaseModel):
    status: str


class NotifyStaffRequest(BaseModel):
    description: str


class StaffRole(str, enum.Enum):
    JANITOR = "JANITOR"
    VETERINARIAN = "VETERINARIAN"
    COORDINATOR = "COORDINATOR"
    ZOOKEEPER = "ZOOKEEPER"


class AnimalStatus(BaseModel):
    time: datetime = datetime.now()
    status: str
    user_role: StaffRole
    user_id: str


class Animal(BaseModel):
    id: str
    name: str
    specie: str
    age: int
    last_status: list[AnimalStatus]


class StaffNotification(BaseModel):
    time: datetime = datetime.now()
    description: str
    destination_role: StaffRole
    notifier_role: StaffRole
    notifier_id: str