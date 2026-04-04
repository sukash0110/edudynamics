TASKS = {
    "easy": {
        "name": "easy",
        "days": 5,
        "max_energy": 10,
        "daily_target": 4.0,
        "decay_rate": 0.01,
        "consolidation_rate": 0.03,
        "spacing_target": 1,
        "initial_mastery": {"math": 0.25, "physics": 0.2, "chemistry": 0.3},
    },
    "medium": {
        "name": "medium",
        "days": 10,
        "max_energy": 10,
        "daily_target": 5.0,
        "decay_rate": 0.014,
        "consolidation_rate": 0.028,
        "spacing_target": 2,
        "initial_mastery": {"math": 0.2, "physics": 0.15, "chemistry": 0.25},
    },
    "hard": {
        "name": "hard",
        "days": 15,
        "max_energy": 10,
        "daily_target": 6.0,
        "decay_rate": 0.018,
        "consolidation_rate": 0.024,
        "spacing_target": 2,
        "initial_mastery": {"math": 0.1, "physics": 0.08, "chemistry": 0.12},
    },
}


def get_task_config(name):
    if name not in TASKS:
        available = ", ".join(sorted(TASKS))
        raise ValueError(f"Unknown task '{name}'. Available tasks: {available}")
    config = TASKS[name].copy()
    config["initial_mastery"] = TASKS[name]["initial_mastery"].copy()
    return config
