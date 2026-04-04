import os

import uvicorn
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.responses import FileResponse, HTMLResponse, JSONResponse
from streamlit.web.server.starlette.starlette_app import App as StreamlitApp

from study_env.api import app as api_app, session
from study_env.models import ResetRequest, StateModel, StepRequest
from study_env.tasks import TASKS, get_task_config


def landing_page(_request):
    return HTMLResponse(
        """
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
                <img src="/logo" alt="EduDynamics logo" />
                <div>
                  <div class="brand-title">EduDynamics</div>
                  <div class="brand-copy">Running on AuraUI 1.1.0 with stability improvements, liquid-glass simulation, and retention-aware learning dynamics.</div>
                </div>
              </div>
              <div class="actions">
                <a class="button primary" href="/ui" target="_blank">Open Full UI</a>
                <a class="button" href="/api/docs" target="_blank">API Docs</a>
                <a class="button" href="/health" target="_blank">Validation UI</a>
              </div>
            </div>
            <div class="frame-wrap">
              <iframe src="/ui" title="EduDynamics on AuraUI 1.1.0"></iframe>
            </div>
          </body>
        </html>
        """
    )


def logo(_request):
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui", "assets", "edudynamics-logo.svg")
    return FileResponse(logo_path, media_type="image/svg+xml")


def health(_request):
    return JSONResponse(
        {
            "status": "ok",
            "name": "edudynamics",
            "available_tasks": list(TASKS.keys()),
            "current_task": session.current_task(),
        }
    )


def tasks(_request):
    return JSONResponse([get_task_config(name) for name in TASKS])


def state(_request):
    return JSONResponse(StateModel(**session.state()).model_dump())


async def reset(request: Request):
    payload = await request.json() if request.method == "POST" else {}
    reset_request = ResetRequest(**payload)
    observation = StateModel(**session.reset(reset_request)).model_dump()
    return JSONResponse({"observation": observation, "done": False, "info": {"message": "environment reset"}})


async def step(request: Request):
    payload = await request.json()
    step_request = StepRequest(**payload)
    observation, reward, done, info = session.step(step_request.action)
    return JSONResponse(
        {
            "observation": StateModel(**observation).model_dump(),
            "reward": reward,
            "done": done,
            "info": info,
        }
    )


routes = [
    Route("/", endpoint=landing_page),
    Route("/logo", endpoint=logo),
    Route("/health", endpoint=health),
    Route("/tasks", endpoint=tasks),
    Route("/state", endpoint=state),
    Route("/reset", endpoint=reset, methods=["POST"]),
    Route("/step", endpoint=step, methods=["POST"]),
    Mount("/api", app=api_app),
    Mount("/ui", app=StreamlitApp("app.py")),
]

app = StreamlitApp("app.py", routes=routes)


def main():
    port = int(os.getenv("PORT", "8501"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
