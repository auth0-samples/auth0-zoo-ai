import os

import requests
from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from auth0_fastapi.server.routes import router, register_auth_routes

from agent import run_agent
from auth import auth_config, auth_client, get_access_token

import logging

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


@app.post("/prompt")
async def query_genai(
    data: Prompt, 
    request: Request,
    auth_session = Depends(auth_client.require_session),
):
    
    result = await run_agent(
        data.prompt,
        user_role=auth_session['user']['https://zooai/roles'][0],
        user_id=auth_session['user']['sub'],
        token=await get_access_token(request),
    )
    return {"response": result}


@app.get("/staff_notifications")
async def get_staff_notifications(request: Request):
    
    access_token = await get_access_token(request)
    response = requests.get(
        f"{os.getenv('API_BASE_URL')}/staff/notification",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()
