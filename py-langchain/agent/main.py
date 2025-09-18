import logging
import os
from datetime import datetime
from typing import Iterable, Literal

import requests
import uvicorn
from auth import auth_client, auth_config, get_access_token
from auth0_fastapi.server.routes import register_auth_routes, router
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import AIMessage, HumanMessage
from langgraph_sdk import get_client
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

langgraph_client = get_client(url=os.getenv("LANGGRAPH_URL", "http://localhost:2024"))


async def get_thread(request: Request) -> dict:
    try:
        thread_id = await get_thread_id(request)
        thread = await langgraph_client.threads.get(thread_id)
    except:
        thread_id = await get_thread_id(request, create_new=True)
        thread = await langgraph_client.threads.get(thread_id)
    return thread


async def get_thread_id(request: Request, create_new=False) -> str:
    if "thread_id" not in request.session or create_new:
        logging.info("Creating new thread")
        thread = await langgraph_client.threads.create()
        request.session["thread_id"] = thread["thread_id"]

    return request.session["thread_id"]


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
    type: Literal["human", "ai", "interrupted"] = "human"


@app.get("/prompt")
async def get_prompt(
    request: Request,
    auth_session=Depends(auth_client.require_session),
) -> Iterable[Prompt]:

    thread = await get_thread(request)
    messages = []
    if "values" in thread and "messages" in thread["values"]:
        messages = list(
            filter(None, map(_convert_to_prompt, thread["values"]["messages"]))
        )

    interrupts = thread.get("interrupts", {})
    for interrupt in interrupts.values():
        messages.append(
            Prompt(prompt=interrupt[0]["value"]["message"], type="interrupted")
        )

    return messages


@app.get("/prompt/new")
async def get_new_prompt(request: Request, response: Response):
    await get_thread_id(request, create_new=True)
    return RedirectResponse(url="/")


def _convert_to_prompt(message: HumanMessage | AIMessage) -> Prompt | None:

    if message["type"] not in ["human", "ai"]:
        return None

    content = message["content"]

    if not content:
        return None

    marker = "User input:"

    if marker in content:
        content = content.split(marker, 1)[1].strip()

    return Prompt(prompt=content, type=message["type"])


@app.post("/prompt")
async def query_genai(
    data: Prompt,
    request: Request,
    response: Response,
    auth_session=Depends(auth_client.require_session),
):
    user_role = auth_session["user"]["https://zooai/roles"][0]
    access_token = await get_access_token(request, response)
    refresh_token = auth_session.get("refresh_token")

    result = await langgraph_client.runs.wait(
        thread_id=await get_thread_id(request),
        assistant_id="agent",
        input={
            "messages": [
                HumanMessage(
                    content=f"User role: {user_role}. Timestamp: {datetime.now().isoformat()}, User input: {data.prompt}"
                )
            ]
        },
        config={
            "configurable": {
                "_credentials": {"refresh_token": refresh_token},
                "api_access_token": access_token,
            }
        },
    )

    return {"response": result["messages"][-1]["content"]}


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
