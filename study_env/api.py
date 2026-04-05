from threading import Lock
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse

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
            return self._env.reset()

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


session = EnvironmentSession()
app = FastAPI(title="EduDynamics API", version="1.1.0")


@app.get("/", response_model=HealthResponse)
def root():
    return HealthResponse(
        status="ok",
        name="edudynamics",
        available_tasks=list(TASKS.keys()),
        current_task=session.current_task(),
    )


@app.get("/health", response_model=HealthResponse)
def health():
    return root()


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
            "required_env": ["API_BASE_URL", "MODEL_NAME", "HF_TOKEN", "OPENAI_API_KEY"],
            "actions": session.state()["action_meanings"],
            "tasks": list(TASKS.keys()),
        }
    )
