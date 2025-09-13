import logging

from dotenv import load_dotenv
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.llms.openai import OpenAI

from tools_async_auth import emergency_protocol_tool
from agent_context import get_agent_context, clean_agent_context
from tools_api_call import list_animals_tool, notify_staff_tool, update_animal_status_tool
from tools_thirdparty_api_call import (ask_for_cleaning_supplies_tool,
                                       ask_for_veterinarian_supplies_tool)

logger = logging.getLogger(__name__)

load_dotenv()


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
9. Veterinarians can ask for medical supplies to be delivered to an animal. If a supplied is asked, keep an annotation in the animal database.
10. Zookeepers can ask for cleaning supplies to be delivered to a specific location.
11. Coordinators can ask for any kind of supplies.
12. If the user is referring to a staff group, notify the staff group of the event.


If you are unsure about an action or if critical information is missing, ask for clarification.
Prioritize safety and adherence to zoo protocols.

Begin!

"""

tools = [
    ## ADD YOUR TOOLS HERE
    list_animals_tool,
    update_animal_status_tool,
    notify_staff_tool,
    ask_for_veterinarian_supplies_tool,
    ask_for_cleaning_supplies_tool,
    emergency_protocol_tool
]

_LLM = OpenAI(model="gpt-4o-mini")
_agent = FunctionAgent(
    tools=tools,
    llm=_LLM,
    system_prompt=SYSTEM_MESSAGE_PREFIX,
)

_chat_store = SimpleChatStore()

async def _get_memory(user_id:str, chat_id: str):
    return ChatMemoryBuffer.from_defaults(
        token_limit=3000,
        chat_store=_chat_store,
        chat_store_key=f"{user_id}_{chat_id}",
    )


async def run_agent(
    user_input: str, user_role: str, user_id: str, chat_id: str, refresh_token: str = None, access_token: str = None
):

    try:
        context = get_agent_context()
        context["refresh_token"] = refresh_token
        context["access_token"] = access_token
        memory = await _get_memory(user_id, chat_id)
        return await _agent.run(user_msg=user_input, memory=memory)
    finally:
        clean_agent_context()


async def get_messages(user_id: str, chat_id: str):
    store = await _get_memory(user_id, chat_id)
    return store.chat_store.get_messages(f"{user_id}_{chat_id}")
