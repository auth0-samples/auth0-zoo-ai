import logging
from datetime import datetime
from typing import Annotated, Iterable, TypedDict

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import END, START
from langgraph.graph import StateGraph, add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from zoo_tools import list_animals, notify_staff, update_animal_status
from tools_thirdparty_api_call import (ask_for_cleaning_supplies_tool,
                                       ask_for_veterinarian_supplies_tool)
from tools_async_auth import emergency_protocol_tool

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
    list_animals,
    update_animal_status,
    notify_staff,
    ask_for_veterinarian_supplies_tool,
    ask_for_cleaning_supplies_tool,
    emergency_protocol_tool
]


class State(TypedDict):
    messages: Annotated[list, add_messages]


__LLM = init_chat_model("openai:gpt-4o-mini").bind_tools(tools)


async def chatbot(state: State) -> State:

    request_messages = state.get("messages")
    if not request_messages or len(request_messages) == 1:
        initial = SystemMessage(SYSTEM_MESSAGE_PREFIX)
        request_messages = [initial, request_messages[0]]
        state["messages"] = request_messages

    response_messages = await __LLM.ainvoke(request_messages)

    if isinstance(response_messages, list):
        state["messages"].extend(response_messages)
    else:
        state["messages"].append(response_messages)
    return state


def create_langgraph():
    graph_builder = StateGraph(State)
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", ToolNode(tools))
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("chatbot", END)
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_conditional_edges("chatbot", tools_condition)
    return graph_builder.compile(checkpointer=InMemorySaver())


__GRAPH = create_langgraph()


async def run_agent(
    user_input: str, user_role: str, user_id: str, token: str, refresh_token: str
) -> str:
    config = {
        "configurable": {
            "thread_id": user_id,
            "_credentials": {"refresh_token": refresh_token},
            "api_access_token": token,
        }
    }
    message = HumanMessage(
        content=f"User role: {user_role}. Timestamp: {datetime.now().isoformat()}, User input: {user_input}"
    )

    initial_state = State(messages=[message])

    response = await __GRAPH.ainvoke(
        initial_state,
        config=config,
    )

    return response["messages"][-1].content


async def get_messages(user_id: str) -> Iterable[HumanMessage | AIMessage]:
    config = {
        "configurable": {
            "thread_id": user_id,
        }
    }
    snapshot = __GRAPH.get_state(config=config)
    return filter(
        lambda message: isinstance(message, (HumanMessage, AIMessage)),
        snapshot.values.get("messages", []),
    )
