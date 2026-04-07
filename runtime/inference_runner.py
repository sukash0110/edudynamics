import argparse
import json
import os
import random

from openai import OpenAI

from study_env import StudyPlannerEnv
from study_env.tasks import TASKS
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
API_KEY = os.getenv("API_KEY", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME", "")
BENCHMARK_NAME = "edudynamics"


class DeterministicPlannerAgent:
    def __init__(self, stochastic_tie_break=False, seed=123):
        self.last_action = None
        self.stochastic_tie_break = stochastic_tie_break
        self.seed = seed

    def act(self, observation):
        energy = observation["energy"]
        mastery = observation["mastery"]
        imbalance = observation["imbalance"]
        retention_risk = observation.get("retention_risk", {})
        cognitive_load = observation.get("cognitive_load", 0.0)
        weakest_subject = min(mastery, key=mastery.get)
        strongest_subject = max(mastery, key=mastery.get)
        highest_risk_subject = max(retention_risk, key=retention_risk.get) if retention_risk else weakest_subject

        if energy <= 2.5 or cognitive_load >= 0.86:
            action = 6
        elif retention_risk and retention_risk[highest_risk_subject] >= 0.64:
            action = {"math": 3, "physics": 4, "chemistry": 5}[highest_risk_subject]
        elif imbalance >= 0.18:
            action = {"math": 3, "physics": 4, "chemistry": 5}[weakest_subject]
        elif mastery[weakest_subject] <= 0.72:
            action = {"math": 0, "physics": 1, "chemistry": 2}[weakest_subject]
        elif mastery[strongest_subject] - mastery[weakest_subject] >= 0.1:
            action = {"math": 3, "physics": 4, "chemistry": 5}[weakest_subject]
        else:
            ordered = sorted(mastery.items(), key=lambda item: (item[1], item[0]))
            lowest_value = ordered[0][1]
            lowest_subjects = [subject for subject, value in ordered if value == lowest_value]
            if self.stochastic_tie_break and len(lowest_subjects) > 1:
                base_seed = self.seed if self.seed is not None else 0
                index = (observation["day"] + observation["slot"] + base_seed) % len(lowest_subjects)
                subject = lowest_subjects[index]
            else:
                subject = ordered[0][0]
            action = {"math": 0, "physics": 1, "chemistry": 2}[subject]

        self.last_action = action
        return action


class OpenAIBaselineAgent:
    def __init__(self, model_name=None, api_key=None, api_base_url=None):
        self.model_name = model_name or MODEL_NAME
        self.api_key = api_key or API_KEY or os.getenv("OPENAI_API_KEY") or HF_TOKEN
        self.api_base_url = api_base_url or API_BASE_URL
        if not self.api_key:
            raise ValueError("API_KEY, HF_TOKEN, or OPENAI_API_KEY is required for OpenAIBaselineAgent.")
        client_kwargs = {"api_key": self.api_key}
        if self.api_base_url:
            client_kwargs["base_url"] = self.api_base_url
        self.client = OpenAI(**client_kwargs)

    def _build_prompt(self, observation):
        action_meanings = observation["action_meanings"]
        return (
            "You are choosing the next action in EduDynamics, a student study planning environment.\n"
            "Pick exactly one action id that best improves long-term performance while preserving balance and energy.\n"
            "Return strict JSON with keys action and rationale.\n\n"
            f"Observation:\n{json.dumps(observation, indent=2)}\n\n"
            f"Available actions:\n{json.dumps(action_meanings, indent=2)}\n"
        )

    def act(self, observation):
        response = self.client.responses.create(
            model=self.model_name,
            temperature=0,
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "You are a deterministic planning agent. "
                                "Always return valid JSON with an integer action from 0 to 6."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": self._build_prompt(observation)}],
                },
            ],
        )
        text = response.output_text.strip()
        payload = json.loads(text)
        action = int(payload["action"])
        if action < 0 or action > 6:
            raise ValueError(f"Model returned invalid action: {action}")
        return action


def run_episode(task_name, stochastic=False, seed=123, agent_mode="heuristic"):
    env = StudyPlannerEnv(task_name=task_name, stochastic=stochastic, seed=seed)
    if agent_mode == "openai":
        agent = OpenAIBaselineAgent()
    else:
        agent = DeterministicPlannerAgent(stochastic_tie_break=stochastic, seed=seed)
    observation = env.reset()
    total_reward = 0.0
    steps = 0
    trace = []

    done = False
    while not done:
        action = agent.act(observation)
        observation, reward, done, info = env.step(action)
        total_reward += reward
        steps += 1
        trace.append(
            {
                "step": steps,
                "day": observation["day"],
                "energy": observation["energy"],
                "avg_mastery": observation["avg_mastery"],
                "imbalance": observation["imbalance"],
                "mastery": observation["mastery"],
                "memory_strength": observation.get("memory_strength", {}),
                "retention_risk": observation.get("retention_risk", {}),
                "cognitive_load": observation.get("cognitive_load", 0.0),
                "recovery_score": observation.get("recovery_score", 0.0),
                "action": info["action"],
                "reward": reward,
                "reward_breakdown": info.get("reward_breakdown", {}),
            }
        )

    summary = {
        "task": task_name,
        "stochastic": stochastic,
        "seed": seed,
        "agent_mode": agent_mode,
        "steps": steps,
        "total_reward": round(total_reward, 4),
        "final_state": observation,
        "episode_summary": info.get("episode_summary", {}),
        "trace": trace,
        "trace_tail": trace[-5:],
    }
    return summary


def _format_action(action_info):
    subject = action_info.get("subject")
    return f"{action_info['type']}:{subject}" if subject else action_info["type"]


def log_start(task_name, model_name):
    print(f"[START] task={task_name} env={BENCHMARK_NAME} model={model_name}", flush=True)


def log_step(step, action_str, reward, done, error=None):
    error_value = error if error else "null"
    print(
        f"[STEP] step={step} action={action_str} reward={reward:.2f} done={str(done).lower()} error={error_value}",
        flush=True,
    )


def log_end(success, steps, rewards):
    rewards_str = ",".join(f"{reward:.2f}" for reward in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} rewards={rewards_str}", flush=True)


def run_logged_episode(task_name, stochastic=False, seed=123, agent_mode="heuristic"):
    env = StudyPlannerEnv(task_name=task_name, stochastic=stochastic, seed=seed)
    if agent_mode == "openai":
        agent = OpenAIBaselineAgent()
        model_name = agent.model_name
    else:
        agent = DeterministicPlannerAgent(stochastic_tie_break=stochastic, seed=seed)
        model_name = "heuristic"

    observation = env.reset()
    rewards = []
    steps_taken = 0
    summary = None
    success = False

    log_start(task_name=task_name, model_name=model_name)

    try:
        done = False
        while not done:
            action = agent.act(observation)
            observation, reward, done, info = env.step(action)
            rewards.append(reward)
            steps_taken += 1
            log_step(steps_taken, _format_action(info["action"]), reward, done, None)

        summary = {
            "task": task_name,
            "stochastic": stochastic,
            "seed": seed,
            "agent_mode": agent_mode,
            "steps": steps_taken,
            "total_reward": round(sum(rewards), 4),
            "final_state": observation,
            "episode_summary": info.get("episode_summary", {}),
            "trace": [],
            "trace_tail": [],
        }
        from evaluation.grader_runner import evaluate_task

        success = evaluate_task(task_name, summary)["passed"]
        return summary
    finally:
        close_fn = getattr(env, "close", None)
        if callable(close_fn):
            close_fn()
        log_end(success=success, steps=steps_taken, rewards=rewards)


def print_summary(summary):
    episode = summary["episode_summary"]
    print(f"Task: {summary['task']}")
    print(f"Agent: {summary['agent_mode']}")
    print(f"Mode: {'stochastic' if summary['stochastic'] else 'deterministic'}")
    if summary["stochastic"]:
        print(f"Seed: {summary['seed']}")
    print(f"Steps: {summary['steps']}")
    print(f"Total reward: {summary['total_reward']}")
    print(f"Final average mastery: {episode.get('average_mastery')}")
    print(f"Final memory strength: {episode.get('average_memory_strength')}")
    print(f"Final balance gap: {episode.get('balance_gap')}")
    print(f"Energy left: {episode.get('energy_left')}")
    print("Trace tail:")
    for item in summary["trace_tail"]:
        action = item["action"]
        print(
            f"  step={item['step']} day={item['day']} energy={item['energy']} "
            f"avg={item['avg_mastery']} imbalance={item['imbalance']} "
            f"action={action['type']}:{action['subject']} reward={item['reward']}"
        )


def main():
    parser = argparse.ArgumentParser(description="Run the EduDynamics baseline agent.")
    parser.add_argument(
        "--stochastic",
        action="store_true",
        help="Enable stochastic environment dynamics for varied runs.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=123,
        help="Seed used when stochastic mode is enabled.",
    )
    parser.add_argument(
        "--randomize",
        action="store_true",
        help="Enable stochastic mode with a different random seed on every run.",
    )
    parser.add_argument(
        "--agent",
        choices=["auto", "openai", "heuristic"],
        default="auto",
        help="Agent backend for inference. 'auto' uses OpenAI when OPENAI_API_KEY is set, else heuristic.",
    )
    args = parser.parse_args()

    stochastic = args.stochastic or args.randomize
    seed = random.SystemRandom().randint(0, 10**9) if args.randomize else args.seed
    if args.agent == "auto":
        agent_mode = "openai" if (API_KEY or os.getenv("OPENAI_API_KEY")) else "heuristic"
    else:
        agent_mode = args.agent

    for task_name in TASKS:
        run_logged_episode(task_name, stochastic=stochastic, seed=seed, agent_mode=agent_mode)


if __name__ == "__main__":
    main()
