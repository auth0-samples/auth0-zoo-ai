import os

from dotenv import load_dotenv
from fastapi import Depends, Request, HTTPException, status
from auth0_fastapi.auth import AuthClient
from auth0_fastapi.config import Auth0Config

load_dotenv()

auth_config = Auth0Config(
    domain=os.getenv("AUTH0_DOMAIN"),
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
    audience=os.getenv("API_AUDIENCE"),
    authorization_params={
        "scope": "openid profile email offline_access",
        "prompt": "consent"
    },
    app_base_url=os.getenv("APP_BASE_URL", "http://localhost:3000"),
    secret=os.getenv("APP_SECRET_KEY", "SOME_RANDOM_SECRET_KEY"),
    mount_connect_routes=True
)


auth_client = AuthClient(auth_config)


def get_user_role (auth_session = Depends(auth_client.require_session)) -> str:
    roles = auth_session.user.get("https://zooai/roles", [])

    if not roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no roles assigned"
        )
    
    if len(roles) != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User must have exactly one role, found: {roles}"
        )        

    return roles[0]


async def get_access_token(request: Request) -> str:
    store_options = {"request": request}
    return await auth_client.client.get_access_token(store_options=store_options)