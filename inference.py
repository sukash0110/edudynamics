import argparse
import random

from study_env import StudyPlannerEnv
from study_env.tasks import TASKS


class DeterministicPlannerAgent:
    def __init__(self, stochastic_tie_break=False, seed=123):
        self.last_action = None
        self.stochastic_tie_break = stochastic_tie_break
        self.seed = seed

    def act(self, observation):
        energy = observation["energy"]
        mastery = observation["mastery"]
        imbalance = observation["imbalance"]
        weakest_subject = min(mastery, key=mastery.get)
        strongest_subject = max(mastery, key=mastery.get)

        if energy <= 2.5:
            action = 6
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


def run_episode(task_name, stochastic=False, seed=123):
    env = StudyPlannerEnv(task_name=task_name, stochastic=stochastic, seed=seed)
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
                "action": info["action"],
                "reward": reward,
            }
        )

    summary = {
        "task": task_name,
        "stochastic": stochastic,
        "seed": seed,
        "steps": steps,
        "total_reward": round(total_reward, 4),
        "final_state": observation,
        "episode_summary": info.get("episode_summary", {}),
        "trace": trace,
        "trace_tail": trace[-5:],
    }
    return summary


def print_summary(summary):
    episode = summary["episode_summary"]
    print(f"Task: {summary['task']}")
    print(f"Mode: {'stochastic' if summary['stochastic'] else 'deterministic'}")
    if summary["stochastic"]:
        print(f"Seed: {summary['seed']}")
    print(f"Steps: {summary['steps']}")
    print(f"Total reward: {summary['total_reward']}")
    print(f"Final average mastery: {episode.get('average_mastery')}")
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
    args = parser.parse_args()

    stochastic = args.stochastic or args.randomize
    seed = random.SystemRandom().randint(0, 10**9) if args.randomize else args.seed

    for task_name in TASKS:
        summary = run_episode(task_name, stochastic=stochastic, seed=seed)
        print_summary(summary)
        print("-" * 60)


if __name__ == "__main__":
    main()
