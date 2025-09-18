import logging

import uvicorn
from auth import get_user_id, get_user_role, require_authenticated_user
from catalog import AnimalCatalog, ItemNotFound, StaffNotificationCatalog
from dependencies import get_animal_catalog, get_staff_notification_catalog
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from schema import (Animal, AnimalStatus, NotifyStaffRequest,
                    StaffNotification, StaffRole, UpdateAnimalStatusRequest)

logger = logging.getLogger(__name__)
app = FastAPI()


@app.exception_handler(ItemNotFound)
async def animal_not_found_exception_handler(request, exception):
    return JSONResponse(
        status_code=404,
        content={"message": "Item not found"},
    )


@app.post("/animal/{animal_id}/status")
def update_animal_status(
    data: UpdateAnimalStatusRequest,
    animal_id: str,
    user_claims=Depends(require_authenticated_user),
    animal_catalog: AnimalCatalog = Depends(get_animal_catalog),
):
    animal_catalog.add_status(
        animal_id,
        AnimalStatus(
            status=data.status,
            user_role=get_user_role(user_claims),
            user_id=get_user_id(user_claims),
        ),
    )


@app.get("/animal")
def list_animals(
    user_claims=Depends(require_authenticated_user),
    animal_catalog: AnimalCatalog = Depends(get_animal_catalog),
) -> list[Animal]:
    return animal_catalog.get_all()


@app.get("/staff/notification")
def get_staff_notification(
    role: StaffRole = Depends(get_user_role),
    staff_catalog: StaffNotificationCatalog = Depends(get_staff_notification_catalog),
) -> list[StaffNotification]:
    return staff_catalog.get_notifications_by_role(role)


@app.post("/staff/notification/{role}")
def notify_staff(
    role: StaffRole,
    notification: NotifyStaffRequest,
    user_claims=Depends(require_authenticated_user),
    staff_catalog: StaffNotificationCatalog = Depends(get_staff_notification_catalog),
):
    logger.info("Storing notification for role %s: %s", role, notification.description)
    staff_catalog.add_notification(
        StaffNotification(
            notifier_role=get_user_role(user_claims),
            notifier_id=get_user_id(user_claims),
            description=notification.description,
            destination_role=role,
        )
    )


from auth import auth0


@app.put("/emergency")
def start_emergency(
    user_claims=Depends(auth0.require_auth(scopes=["emergency:start"])),
    staff_catalog: StaffNotificationCatalog = Depends(get_staff_notification_catalog),
):
    logger.info("Starting emergency for user %s", get_user_id(user_claims))

    for role in StaffRole:
        staff_catalog.add_notification(
            StaffNotification(
                notifier_role=get_user_role(user_claims),
                notifier_id=get_user_id(user_claims),
                description="Emergency protocol started. Close the ZOO and put visitors in a safe locations. Further instructions will be sent as soon as possible.",
                destination_role=role,
            )
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
