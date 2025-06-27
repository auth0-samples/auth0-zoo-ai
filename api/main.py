import logging
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from auth import require_authenticated_user, get_user_id, get_user_role
from dependencies import get_animal_catalog, get_staff_notification_catalog
from catalog import AnimalCatalog, ItemNotFound, StaffNotificationCatalog

from schema import (
    Animal,
    AnimalStatus,
    NotifyStaffRequest,
    StaffNotification,
    StaffRole,
    UpdateAnimalStatusRequest,
)

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
            status=data.status, user_role=get_user_role(user_claims), user_id=get_user_id(user_claims)
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
    staff_catalog: StaffNotificationCatalog = Depends(
        get_staff_notification_catalog
    ),

) -> list[StaffNotification]:
    return staff_catalog.get_notifications_by_role(role)

@app.post("/staff/notification/{role}")
def notify_staff(
    role: StaffRole,
    notification: NotifyStaffRequest,
    user_claims=Depends(require_authenticated_user),
    staff_catalog: StaffNotificationCatalog = Depends(
        get_staff_notification_catalog
    ),

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