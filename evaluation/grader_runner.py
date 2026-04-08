import math

from runtime.inference_runner import run_episode
from study_env.tasks import TASKS


TASK_THRESHOLDS = {
    "easy": {"min_reward": 6.5, "min_mastery": 0.72, "max_balance_gap": 0.18, "min_deadline_readiness": 0.72},
    "medium": {"min_reward": 13.0, "min_mastery": 0.95, "max_balance_gap": 0.08, "min_deadline_readiness": 0.9},
    "hard": {"min_reward": 11.5, "min_mastery": 0.95, "max_balance_gap": 0.08, "min_deadline_readiness": 0.92},
}


def _clip(value, eps=0.01):
    if not math.isfinite(value):
        return 0.5
    value = max(eps, min(1.0 - eps, value))
    value = round(value, 2)
    if value <= 0.0:
        return eps
    if value >= 1.0:
        return 1.0 - eps
    return value


def evaluate_task(task_name, summary):
    episode = summary["episode_summary"]
    thresholds = TASK_THRESHOLDS[task_name]

    reward_score = _clip(summary["total_reward"] / thresholds["min_reward"])
    mastery_score = _clip(episode["average_mastery"] / thresholds["min_mastery"])
    balance_score = _clip(thresholds["max_balance_gap"] / max(episode["balance_gap"], 0.0001))
    readiness_score = _clip(episode.get("deadline_readiness", 0.0) / thresholds["min_deadline_readiness"])

    checks = {
        "reward_ok": summary["total_reward"] >= thresholds["min_reward"],
        "mastery_ok": episode["average_mastery"] >= thresholds["min_mastery"],
        "balance_ok": episode["balance_gap"] <= thresholds["max_balance_gap"],
        "deadline_ready_ok": episode.get("deadline_readiness", 0.0) >= thresholds["min_deadline_readiness"],
    }
    score = _clip((reward_score + mastery_score + balance_score + readiness_score) / 4.0)

    return {
        "task": task_name,
        "score": score,
        "passed": all(checks.values()),
        "checks": checks,
        "thresholds": thresholds,
        "metrics": {
            "total_reward": summary["total_reward"],
            "average_mastery": episode["average_mastery"],
            "balance_gap": episode["balance_gap"],
            "deadline_readiness": episode.get("deadline_readiness", 0.0),
            "energy_left": episode["energy_left"],
            "steps": summary["steps"],
        },
    }


def grade():
    task_results = {}
    aggregate_score = 0.0
    passed_tasks = 0

    for task_name in TASKS:
        summary = run_episode(task_name, stochastic=False, seed=123, agent_mode="heuristic")
        evaluation = evaluate_task(task_name, summary)
        task_results[task_name] = evaluation
        aggregate_score += evaluation["score"]
        passed_tasks += int(evaluation["passed"])

    overall_score = _clip(aggregate_score / len(TASKS))
    overall_status = "pass" if passed_tasks == len(TASKS) else "partial"

    return {
        "overall_status": overall_status,
        "overall_score": overall_score,
        "passed_tasks": passed_tasks,
        "total_tasks": len(TASKS),
        "task_results": task_results,
    }


def main():
    result = grade()
    print("Deterministic grading summary")
    print(
        f"overall_status={result['overall_status']} "
        f"overall_score={result['overall_score']} "
        f"passed_tasks={result['passed_tasks']}/{result['total_tasks']}"
    )

    for task_name, evaluation in result["task_results"].items():
        metrics = evaluation["metrics"]
        print(
            f"{task_name}: score={evaluation['score']}, "
            f"passed={evaluation['passed']}, "
            f"reward={metrics['total_reward']}, "
            f"avg_mastery={metrics['average_mastery']}, "
            f"balance_gap={metrics['balance_gap']}, "
            f"energy_left={metrics['energy_left']}, steps={metrics['steps']}"
        )


if __name__ == "__main__":
    main()
