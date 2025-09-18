import logging
import os

import requests
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from pydantic import BaseModel, Field

load_dotenv()

logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("API_BASE_URL")


def _get_headers(config: RunnableConfig) -> dict:
    access_token = config.get("configurable", {}).get("api_access_token")
    return {"Authorization": f"Bearer {access_token}"}


@tool
def list_animals(event: str, config: RunnableConfig) -> list[dict]:
    """Get the list of all animals and their IDs."""
    try:
        logger.info("list animals %s", event)
        response = requests.get(f"{API_BASE_URL}/animal", headers=_get_headers(config))
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.exception("error")
        raise e


class UpdateAnimalStatusArgs(BaseModel):
    animal_id: str = Field(..., description="ID of the animal to update")
    event_description: str = Field(
        ..., description="Clear and concise description of the event"
    )


@tool(args_schema=UpdateAnimalStatusArgs)
def update_animal_status(
    animal_id: str, event_description: str, config: RunnableConfig
) -> str:
    """Add an event to an animal."""
    logger.info("add animal event %s", event_description)
    response = requests.post(
        f"{API_BASE_URL}/animal/{animal_id}/status",
        headers=_get_headers(config),
        json={"status": event_description},
    )
    response.raise_for_status()
    return "event added"


class NotifyStaffArgs(BaseModel):
    event: str = Field(..., description="Event to notify staff about")
    staff_role: str = Field(
        ...,
        description="Role of the staff to notify. Can be COORDINATOR, VETERINARIAN, JANITOR or ZOOKEEPER",
    )


@tool(args_schema=NotifyStaffArgs)
def notify_staff(event: str, staff_role: str, config: RunnableConfig) -> str:
    """Notify a staff group about an event at the zoo."""
    logger.info("notify staff %s", event)
    response = requests.post(
        f"{API_BASE_URL}/staff/notification/{staff_role}",
        headers=_get_headers(config),
        json={"description": event},
    )
    response.raise_for_status()
    return "notification sent"
