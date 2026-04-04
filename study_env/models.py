from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskConfigModel(BaseModel):
    name: str
    days: int
    max_energy: float
    daily_target: float
    decay_rate: float
    consolidation_rate: float
    spacing_target: int
    initial_mastery: Dict[str, float]


class ResetRequest(BaseModel):
    task_name: str = Field(default="easy")
    stochastic: bool = Field(default=False)
    seed: Optional[int] = Field(default=123)


class StepRequest(BaseModel):
    action: int = Field(ge=0, le=6)


class ActionModel(BaseModel):
    action: int = Field(ge=0, le=6)
    rationale: Optional[str] = None


class RewardModel(BaseModel):
    value: float
    components: Dict[str, float] = Field(default_factory=dict)


class StateModel(BaseModel):
    task: str
    day: int
    slot: int
    remaining_days: int
    energy: float
    energy_ratio: float
    mastery: Dict[str, float]
    memory_strength: Dict[str, float]
    retention_risk: Dict[str, float]
    avg_mastery: float
    imbalance: float
    daily_target: float
    cognitive_load: float
    recovery_score: float
    stochastic: bool
    seed: Optional[int]
    action_meanings: Dict[int, str]


class ResetResponse(BaseModel):
    observation: StateModel
    done: bool
    info: Dict[str, Any]


class StepResponse(BaseModel):
    observation: StateModel
    reward: float
    done: bool
    info: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    name: str
    available_tasks: List[str]
    current_task: Optional[str]


class ValidationReport(BaseModel):
    overall_status: str
    overall_score: float
    passed_tasks: int
    total_tasks: int
    task_results: Dict[str, Any]
