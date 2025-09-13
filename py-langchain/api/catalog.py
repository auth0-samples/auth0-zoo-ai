from datetime import datetime
from sqlite3 import Connection

from schema import Animal, AnimalStatus, StaffNotification, StaffRole


class ItemNotFound(Exception):
    pass


class AnimalCatalog:
    def __init__(self, conn: Connection):
        self.conn = conn

    def get_all(self) -> list[Animal]:
        cursor = self.conn.execute("SELECT * FROM animal")
        animals = []
        for row in cursor.fetchall():
            animal_id, name, specie, age = row
            statuses = self._get_statuses(animal_id)
            animals.append(
                Animal(
                    id=animal_id,
                    name=name,
                    specie=specie,
                    age=age,
                    last_status=statuses,
                )
            )
        return animals

    def _get_statuses(self, animal_id: str) -> list[AnimalStatus]:
        cursor = self.conn.execute(
            "SELECT time, status, user_role, user_id FROM animal_status WHERE animal_id = ? ORDER BY time DESC",
            (animal_id,),
        )
        return [
            AnimalStatus(
                time=datetime.fromisoformat(t), status=s, user_role=r, user_id=u
            )
            for t, s, r, u in cursor.fetchall()
        ]

    def add_status(self, animal_id: str, status: AnimalStatus):
        cursor = self.conn.execute("SELECT 1 FROM animal WHERE id = ?", (animal_id,))
        if not cursor.fetchone():
            raise ItemNotFound()

        self.conn.execute(
            "INSERT INTO animal_status (animal_id, time, status, user_role, user_id) VALUES (?, ?, ?, ?, ?)",
            (
                animal_id,
                status.time.isoformat(),
                status.status,
                status.user_role,
                status.user_id,
            ),
        )
        self.conn.commit()


class StaffNotificationCatalog:
    def __init__(self, conn: Connection):
        self.conn = conn

    def get_notifications_by_role(
        self, staff_role: StaffRole
    ) -> list[StaffNotification]:
        cursor = self.conn.execute(
            "SELECT time, description, destination_role, notifier_role, notifier_id FROM staff_notification WHERE destination_role = ?",
            (staff_role.value,),
        )
        return [
            StaffNotification(
                time=datetime.fromisoformat(t),
                description=desc,
                destination_role=dest,
                notifier_role=notifier,
                notifier_id=notifier_id,
            )
            for t, desc, dest, notifier, notifier_id in cursor.fetchall()
        ]

    def add_notification(self, notification: StaffNotification):
        self.conn.execute(
            "INSERT INTO staff_notification (time, description, destination_role, notifier_role, notifier_id) VALUES (?, ?, ?, ?, ?)",
            (
                notification.time.isoformat(),
                notification.description,
                notification.destination_role.value,
                notification.notifier_role.value,
                notification.notifier_id,
            ),
        )
        self.conn.commit()
