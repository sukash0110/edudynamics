import asyncio
from urllib.parse import urlencode

import httpx
import websockets
from threading import Lock
from typing import Optional

from fastapi import FastAPI
from fastapi import Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, Response

from .env import StudyPlannerEnv
from .models import HealthResponse, ResetRequest, ResetResponse, StateModel, StepRequest, StepResponse, TaskConfigModel
from .tasks import TASKS, get_task_config


class EnvironmentSession:
    def __init__(self):
        self._lock = Lock()
        self._env: Optional[StudyPlannerEnv] = None

    def reset(self, request: ResetRequest):
        with self._lock:
            self._env = StudyPlannerEnv(
                task_name=request.task_name,
                stochastic=request.stochastic,
                seed=request.seed,
            )
            state = self._env.reset()
            return state

    def step(self, action: int):
        with self._lock:
            if self._env is None:
                self._env = StudyPlannerEnv(task_name="easy")
                self._env.reset()
            return self._env.step(action)

    def state(self):
        with self._lock:
            if self._env is None:
                self._env = StudyPlannerEnv(task_name="easy")
                self._env.reset()
            return self._env.state()

    def current_task(self):
        with self._lock:
            return None if self._env is None else self._env.task_name


app = FastAPI(title="EduDynamics", version="1.0.0")
session = EnvironmentSession()
STREAMLIT_UPSTREAM = "http://127.0.0.1:8502"
STREAMLIT_WS_UPSTREAM = "ws://127.0.0.1:8502"


@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>EduDynamics</title>
        <style>
          body {
            margin: 0;
            font-family: Segoe UI, Arial, sans-serif;
            background: linear-gradient(180deg, #f4f7f4 0%, #eef4ff 100%);
            color: #0f172a;
          }
          .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 18px 28px;
            background: rgba(255, 255, 255, 0.92);
            border-bottom: 1px solid rgba(15, 23, 42, 0.08);
            position: sticky;
            top: 0;
            z-index: 20;
            backdrop-filter: blur(10px);
          }
          .brand {
            display: flex;
            align-items: center;
            gap: 14px;
          }
          .brand img {
            width: 56px;
            height: 56px;
            border-radius: 16px;
          }
          .brand-title {
            font-size: 1.2rem;
            font-weight: 800;
          }
          .brand-copy {
            font-size: 0.92rem;
            color: #475569;
          }
          .actions {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
          }
          .button {
            text-decoration: none;
            padding: 10px 16px;
            border-radius: 999px;
            font-weight: 700;
            border: 1px solid rgba(15, 23, 42, 0.1);
            color: #0f172a;
            background: white;
          }
          .button.primary {
            background: #0f766e;
            color: white;
            border-color: #0f766e;
          }
          .frame-wrap {
            padding: 20px;
          }
          iframe {
            width: 100%;
            height: calc(100vh - 132px);
            border: 0;
            border-radius: 24px;
            box-shadow: 0 16px 40px rgba(15, 23, 42, 0.12);
            background: white;
          }
        </style>
      </head>
      <body>
        <div class="topbar">
          <div class="brand">
            <img src="/assets/edudynamics-logo.svg" alt="EduDynamics logo" />
            <div>
              <div class="brand-title">EduDynamics</div>
              <div class="brand-copy">Streamlit demo plus OpenEnv-compatible API in one Space</div>
            </div>
          </div>
          <div class="actions">
            <a class="button primary" href="/ui" target="_blank">Open Full UI</a>
            <a class="button" href="/docs" target="_blank">API Docs</a>
            <a class="button" href="/health" target="_blank">Health</a>
          </div>
        </div>
        <div class="frame-wrap">
          <iframe src="/ui" title="EduDynamics Streamlit UI"></iframe>
        </div>
      </body>
    </html>
    """


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        name="edudynamics",
        available_tasks=list(TASKS.keys()),
        current_task=session.current_task(),
    )


@app.get("/tasks", response_model=list[TaskConfigModel])
def list_tasks():
    return [TaskConfigModel(**get_task_config(name)) for name in TASKS]


@app.post("/reset", response_model=ResetResponse)
def reset(request: ResetRequest):
    observation = StateModel(**session.reset(request))
    return ResetResponse(observation=observation, done=False, info={"message": "environment reset"})


@app.post("/step", response_model=StepResponse)
def step(request: StepRequest):
    observation, reward, done, info = session.step(request.action)
    return StepResponse(observation=StateModel(**observation), reward=reward, done=done, info=info)


@app.get("/state", response_model=StateModel)
def state():
    return StateModel(**session.state())


@app.get("/spec")
def spec():
    return JSONResponse(
        {
            "name": "edudynamics",
            "required_env": ["API_BASE_URL", "MODEL_NAME", "HF_TOKEN"],
            "actions": session.state()["action_meanings"],
            "tasks": list(TASKS.keys()),
        }
    )


@app.get("/assets/edudynamics-logo.svg")
def logo_asset():
    return Response(
        content=open("assets/edudynamics-logo.svg", "rb").read(),
        media_type="image/svg+xml",
    )


async def _proxy_http(request: Request, path: str = ""):
    upstream_path = f"/ui/{path}" if path else "/ui"
    query_string = request.url.query
    if query_string:
        upstream_path = f"{upstream_path}?{query_string}"
    upstream_url = f"{STREAMLIT_UPSTREAM}{upstream_path}"
    headers = {key: value for key, value in request.headers.items() if key.lower() != "host"}
    body = await request.body()
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.request(
            method=request.method,
            url=upstream_url,
            content=body,
            headers=headers,
        )
    excluded_headers = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    proxy_headers = {key: value for key, value in response.headers.items() if key.lower() not in excluded_headers}
    return Response(response.content, status_code=response.status_code, headers=proxy_headers, media_type=response.headers.get("content-type"))


@app.api_route("/ui", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def proxy_streamlit_root(request: Request):
    return await _proxy_http(request)


@app.api_route("/ui/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def proxy_streamlit(request: Request, path: str):
    return await _proxy_http(request, path)


@app.websocket("/ui/{path:path}")
async def websocket_proxy(websocket: WebSocket, path: str):
    await websocket.accept()
    query = websocket.url.query
    upstream_url = f"{STREAMLIT_WS_UPSTREAM}/ui/{path}"
    if query:
        upstream_url = f"{upstream_url}?{query}"

    async with websockets.connect(upstream_url) as upstream:
        async def client_to_upstream():
            while True:
                message = await websocket.receive()
                if "text" in message and message["text"] is not None:
                    await upstream.send(message["text"])
                elif "bytes" in message and message["bytes"] is not None:
                    await upstream.send(message["bytes"])
                elif message.get("type") == "websocket.disconnect":
                    break

        async def upstream_to_client():
            while True:
                data = await upstream.recv()
                if isinstance(data, bytes):
                    await websocket.send_bytes(data)
                else:
                    await websocket.send_text(data)

        try:
            await asyncio.gather(client_to_upstream(), upstream_to_client())
        except (WebSocketDisconnect, websockets.ConnectionClosed):
            pass
