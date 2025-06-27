import os

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi_plugin import Auth0FastAPI

from schema import StaffRole

load_dotenv()

auth0 = Auth0FastAPI(
    domain=os.getenv("AUTH0_DOMAIN"),
    audience=os.getenv("API_AUDIENCE"),
)

def require_authenticated_user(claims: dict = Depends(auth0.require_auth())):
    return claims

def get_user_role(claims: dict = Depends(require_authenticated_user)) -> StaffRole:
    roles = claims.get("https://zooai/roles", [])  
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
    
    try:
        return StaffRole[roles[0]]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid role: {roles[0]}"
        )

def get_user_name(claims: dict = Depends(require_authenticated_user)) -> str:
    return claims.get("name", "")

def get_user_id(claims: dict = Depends(require_authenticated_user)) -> str:
    return claims.get("sub", "")
