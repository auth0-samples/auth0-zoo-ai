import os

import requests
from auth0_ai.authorizers.ciba.ciba_authorizer_base import get_ciba_credentials
from auth0_ai_langchain.auth0_ai import Auth0AI
from dotenv import load_dotenv
from langchain_core.tools import StructuredTool

load_dotenv()
auth0_ai = Auth0AI()

with_emergency_protocol = auth0_ai.with_async_user_confirmation(
    scopes=["emergency:start"],
    binding_message="Emergency protocol triggered",
    user_id=os.getenv("EMERGENCY_COORDINATOR_ID"),
    audience=os.getenv("API_AUDIENCE"),
)


def emergency_protocol(event: str) -> str:
    credentials = get_ciba_credentials()

    response = requests.put(
        f"{os.getenv('API_BASE_URL')}/emergency",
        headers={
            "authorization": f"{credentials['token_type']} {credentials['access_token']}"
        },
    )
    response.raise_for_status()
    return f"Emergency protocol triggered"


emergency_protocol_tool = with_emergency_protocol(
    StructuredTool.from_function(
        func=emergency_protocol,
        name="emergency_protocol",
        description="Emergency protocols can be triggered by a coordinator.",
    )
)
