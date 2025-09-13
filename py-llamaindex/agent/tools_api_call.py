import logging
import os

import requests
from dotenv import load_dotenv
from llama_index.core.tools import FunctionTool
from pydantic import BaseModel, Field

from agent_context import get_agent_context

load_dotenv()

logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("API_BASE_URL")


def _get_headers() -> dict:
    access_token = get_agent_context()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def list_animals() -> list[dict]:
    """Get the list of all animals and their IDs."""
    try:
        logger.info("list animals")
        response = requests.get(f"{API_BASE_URL}/animal", headers=_get_headers())
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.exception("error")
        raise e

list_animals_tool = FunctionTool.from_defaults(
    name="list_animals",
    description="List all animals in the zoo.",
    fn=list_animals,
)

class UpdateAnimalStatusArgs(BaseModel):
    animal_id: str = Field(..., description="ID of the animal to update")
    event_description: str = Field(
        ..., description="Clear and concise description of the event"
    )


def update_animal_status(
    animal_id: str, event_description: str) -> str:
    """Add an event to an animal."""
    logger.info("add animal event %s", event_description)
    response = requests.post(
        f"{API_BASE_URL}/animal/{animal_id}/status",
        headers=_get_headers(),
        json={"status": event_description},
    )
    response.raise_for_status()
    return "event added"

update_animal_status_tool = FunctionTool.from_defaults(
    name="update_animal_status",
    description="Add an event to an animal.",
    fn=update_animal_status,
    fn_schema=UpdateAnimalStatusArgs,
)


class NotifyStaffArgs(BaseModel):
    event: str = Field(..., description="Event to notify staff about")
    staff_role: str = Field(
        ...,
        description="Role of the staff to notify. Can be COORDINATOR, VETERINARIAN, JANITOR or ZOOKEEPER",
    )


def notify_staff(event: str, staff_role: str) -> str:
    """Notify a staff group about an event at the zoo."""
    logger.info("notify staff %s", event)
    response = requests.post(
        f"{API_BASE_URL}/staff/notification/{staff_role}",
        headers=_get_headers(),
        json={"description": event},
    )
    response.raise_for_status()
    return "notification sent"

notify_staff_tool = FunctionTool.from_defaults(
    name="notify_staff",
    description="Notify a staff group about an event at the zoo.",
    fn=notify_staff,
    fn_schema=NotifyStaffArgs,
)