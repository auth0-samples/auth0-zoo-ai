import logging
import os
import uuid
from typing import Iterable, Literal

import requests
import uvicorn
from llama_cloud import MessageRole

from auth import auth_client, auth_config, get_access_token
from auth0_fastapi.server.routes import register_auth_routes, router
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from agent import get_messages, run_agent

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = FastAPI()

### Setting auth0 authentication
app.add_middleware(SessionMiddleware, secret_key=os.getenv("APP_SECRET_KEY"))

app.state.auth_config = auth_config
app.state.auth_client = auth_client

register_auth_routes(router, auth_config)
app.include_router(router)

### Setting up static files
app.mount("/static", StaticFiles(directory="static"), name="static")

### Setting up app routes


@app.get("/")
async def serve_homepage(request: Request, response: Response):
    try:
        await auth_client.require_session(request, response)
    except Exception as e:
        logging.error(f"Error requiring session: {e}")
        return RedirectResponse(url="/auth/login")

    return FileResponse("static/index.html")


class Prompt(BaseModel):
    prompt: str
    type: Literal["human", "ai"] = "human"


@app.get("/prompt")
async def get_prompt(
        request: Request,
    auth_session=Depends(auth_client.require_session),
) -> Iterable[Prompt]:
    user_id = auth_session["user"]["sub"]

    messages = await get_messages(user_id, get_chat_id(request))
    return filter(None, map(_convert_to_prompt, messages))


def _convert_to_prompt(message) -> Prompt | None:
    type = "human" if message.role == MessageRole.USER else "ai"
    return Prompt(prompt=message.content, type=type)


@app.post("/prompt")
async def query_genai(
    data: Prompt,
    request: Request,
    response: Response,
    auth_session=Depends(auth_client.require_session),
):
    chat_id = get_chat_id(request)

    result = await run_agent(
        data.prompt,
        user_role=auth_session["user"]["https://zooai/roles"][0],
        user_id=auth_session["user"]["sub"],
        access_token=await get_access_token(request, response),
        refresh_token=auth_session.get("refresh_token"),
        chat_id=chat_id,
    )
    return {"response": result.response.content}


def get_chat_id(request):
    if "chatid" not in request.session:
        request.session["chatid"] = str(uuid.uuid4())
    return request.session["chatid"]


@app.get("/staff_notifications")
async def get_staff_notifications(request: Request, response: Response):

    access_token = await get_access_token(request, response)
    response = requests.get(
        f"{os.getenv('API_BASE_URL')}/staff/notification",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
