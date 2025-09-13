import os

import requests
from auth0_ai.authorizers.federated_connection_authorizer import get_access_token_for_connection
from auth0_ai_llamaindex.auth0_ai import Auth0AI
from auth0_ai_llamaindex.ciba import get_access_token
from dotenv import load_dotenv
from llama_index.core.tools import FunctionTool

load_dotenv()
auth0_ai = Auth0AI()

with_emergency_protocol = auth0_ai.with_async_user_confirmation(
    scope="emergency:start",
    binding_message="Emergency protocol triggered",
    user_id=os.getenv("EMERGENCY_COORDINATOR_ID"),
    audience=os.getenv("API_AUDIENCE"),
)


def emergency_protocol(event: str) -> str:
    credentials = get_access_token()

    response = requests.put(
        f"{os.getenv('API_BASE_URL')}/emergency",
        headers={
            "authorization": f"{credentials['type']} {credentials['value']}"
        },
    )
    response.raise_for_status()
    return f"Emergency protocol triggered"


emergency_protocol_tool = with_emergency_protocol(FunctionTool.from_defaults(
        fn=emergency_protocol,
        name="emergency_protocol",
        description="Emergency protocols can be triggered by a coordinator.",
    )
)
