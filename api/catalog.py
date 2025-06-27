from tinydb import Query, TinyDB

from schema import Animal, AnimalStatus, StaffNotification, StaffRole

class ItemNotFound(Exception):
    pass

class AnimalCatalog:
    def __init__(self, db: TinyDB):
        self.table = db.table("animals")
        self.Animal = Query()

    def get_all(self) -> list[Animal]:
        return [Animal(**item) for item in self.table.all()]

    def add_status(self, animal_id: str, status: AnimalStatus):
        result = self.table.search(self.Animal.id == animal_id)
        if not result:
            raise ItemNotFound
        # prepend the new status to the list
        result[0]["last_status"].insert(0, status.model_dump(mode="json"))
        self.table.update(result[0], self.Animal.id == animal_id)

class StaffNotificationCatalog:
    def __init__(self, db: TinyDB):
        self.table = db.table("staff_notification")
        self.StaffNotification = Query()

    def get_notifications_by_role(
        self, staff_role: StaffRole
    ) -> list[StaffNotification]:
        notifications_by_role = self.table.search(
            self.StaffNotification.destination_role == staff_role.value
        )

        return [StaffNotification(**item) for item in notifications_by_role]
    def add_notification(self, notification: StaffNotification):
        self.table.insert(notification.model_dump(mode="json"))
