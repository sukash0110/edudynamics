from inference import run_episode
from study_env.tasks import TASKS


def grade():
    results = {}
    for task_name in TASKS:
        summary = run_episode(task_name, stochastic=False, seed=123)
        episode = summary["episode_summary"]
        results[task_name] = {
            "total_reward": summary["total_reward"],
            "average_mastery": episode["average_mastery"],
            "balance_gap": episode["balance_gap"],
            "energy_left": episode["energy_left"],
            "steps": summary["steps"],
        }
    return results


def main():
    results = grade()
    print("Deterministic grading summary")
    for task_name, metrics in results.items():
        print(
            f"{task_name}: reward={metrics['total_reward']}, "
            f"avg_mastery={metrics['average_mastery']}, "
            f"balance_gap={metrics['balance_gap']}, "
            f"energy_left={metrics['energy_left']}, steps={metrics['steps']}"
        )


if __name__ == "__main__":
    main()
