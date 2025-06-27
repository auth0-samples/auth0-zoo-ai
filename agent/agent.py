import logging
import os
from typing import Callable
from dotenv import load_dotenv
import requests
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")


def _get_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def list_animals_tool(token: str) -> Callable:

    @tool
    def list_animals(event: str) -> list[dict]:
        """Get the list of all animals and their IDs."""
        logger.info("list animals %s", event)

        response = requests.get(
            f"{API_BASE_URL}/animal", headers=_get_headers(token=token)
        )

        response.raise_for_status()
        return response.json()

    return list_animals


class UpdateAnimalStatusArgs(BaseModel):
    animal_id: str = Field(..., description="ID of the animal to update")
    event_description: str = Field(
        ..., description="Clear and concise description of the event"
    )


def update_animal_status_tool(token: str) -> Callable:
    @tool(args_schema=UpdateAnimalStatusArgs)
    def update_animal_status(animal_id: str, event_description: str) -> str:
        """Add an event to an animal."""
        logger.info("add animal event %s", event_description)

        response = requests.post(
            f"{API_BASE_URL}/animal/{animal_id}/status",
            headers=_get_headers(token=token),
            json={"status": event_description},
        )

        response.raise_for_status()
        return "event added"

    return update_animal_status


class NotifyStaffArgs(BaseModel):
    event: str = Field(..., description="Event to notify staff about")
    staff_role: str = Field(
        ...,
        description="Role of the staff to notify. Can be COORDINATOR, VETERINARIAN, JANITOR or ZOOKEEPER",
    )


def notify_staff_tool(token: str) -> Callable:
    @tool(args_schema=NotifyStaffArgs)
    def notify_staff(event: str, staff_role: str) -> str:
        """Notify a staff group about an event at the zoo."""
        logger.info("notify staff %s", event)

        response = requests.post(
            f"{API_BASE_URL}/staff/notification/{staff_role}",
            headers=_get_headers(token=token),
            json={"description": event},
        )

        response.raise_for_status()
        return "notification sent"

    return notify_staff


def _create_tools(token: str) -> list[Callable]:
    return [
        list_animals_tool(token),
        update_animal_status_tool(token),
        notify_staff_tool(token),
    ]


# OpenAI model (you need to export OPENAI_API_KEY)
llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")

SYSTEM_MESSAGE_PREFIX = """
You are the Smart Zoo AI Assistant. Your primary role is to assist zoo staff with managing operations by intelligently using the available tools.
The user's query will be prefixed with their role and user id (e.g., "Role: 'coordinator'. User ID: 'XXXXX'. \\nQuery: \\n ...").
You MUST pay close attention to the user's role to understand their likely permissions and the context of their request.
Before updating an animal status and notify a staff, check if the report was already made to the animal so we can avoid multiple notifications. If this happens, reply to the notifier that the team is already aware.
Base your understanding of roles on the following:
- COORDINATOR: Can report events, update any animal status, and trigger all actions, including emergency protocols.
- VETERINARIAN: Take care of the animals health
- JANITOR: Take care of the zoo public locations, clean the toilets, etc.
- ZOOKEEPER: Take care of the animals, feed them, clean their cages, etc.

All staff can request emergency actions, this action must be confirmed by a coordinator 

Always think step-by-step:
1. Understand the user's intent from their query, username, and role.
2. Consider which tool(s), if any, are appropriate for the request AND the user's role.
3. If the user's role does not permit an action they are requesting, you should state that the action cannot be performed due to role permissions, or suggest an alternative if appropriate.
4. If using a tool, make sure the parameters you provide to the tool are accurate and derived from the user's query.
5.  Provide a clear and helpful response to the user.
6. If the user is referring to an animal, locate the animal in the animal database and update its status with the new event. 
Also, any notification for the users should pass the animal name, location and any other relevant information
7. Events related to medical attention should be logged in the animal database and notified to the staff.
8. Events related to cleaning attention should be logged in the animal database and notified to the staff.

If you are unsure about an action or if critical information is missing, ask for clarification.
Prioritize safety and adherence to zoo protocols.

Begin!

"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_MESSAGE_PREFIX),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)


async def run_agent(user_input: str, user_role: str, user_id: str, token: str) -> str:

    tools = _create_tools(token)
    agent = create_tool_calling_agent(llm, tools, prompt=prompt)

    agent_executor = AgentExecutor(agent=agent, tools=tools)

    message = {
        "input": f"Role: '{user_role}'. User id: '{user_id}'. \nQuery: \n{user_input}"
    }

    logger.info("Query %s", message)

    response = await agent_executor.ainvoke(message)

    return response["output"]
