from copy import deepcopy
import random

from .tasks import get_task_config


class StudyPlannerEnv:
    SUBJECTS = ("math", "physics", "chemistry")
    ACTIONS = {
        0: ("study", "math"),
        1: ("study", "physics"),
        2: ("study", "chemistry"),
        3: ("revise", "math"),
        4: ("revise", "physics"),
        5: ("revise", "chemistry"),
        6: ("rest", None),
    }

    def __init__(self, task_name="easy", stochastic=False, seed=123):
        self.task_name = task_name
        self.stochastic = stochastic
        self.seed = seed
        self.rng = random.Random(seed) if seed is not None else random.Random()
        self.config = get_task_config(task_name)
        self.reset()

    def reset(self):
        self.day = 1
        self.slot = 0
        self.max_days = int(self.config["days"])
        self.max_energy = float(self.config["max_energy"])
        self.daily_target = float(self.config["daily_target"])
        self.energy = float(self.max_energy)
        self.mastery = deepcopy(self.config["initial_mastery"])
        if self.stochastic:
            for subject in self.SUBJECTS:
                offset = self.rng.uniform(-0.05, 0.05)
                self.mastery[subject] = min(1.0, max(0.0, self.mastery[subject] + offset))
        self.history = []
        self.done = False
        return self.state()

    def state(self):
        display_day = min(self.day, self.max_days)
        avg_mastery = sum(self.mastery.values()) / len(self.mastery)
        imbalance = max(self.mastery.values()) - min(self.mastery.values())
        remaining_days = max(0, self.max_days - display_day)
        return {
            "task": self.task_name,
            "day": display_day,
            "slot": self.slot,
            "remaining_days": remaining_days,
            "energy": round(self.energy, 4),
            "energy_ratio": round(self.energy / self.max_energy, 4),
            "mastery": {name: round(value, 4) for name, value in self.mastery.items()},
            "avg_mastery": round(avg_mastery, 4),
            "imbalance": round(imbalance, 4),
            "daily_target": self.daily_target,
            "stochastic": self.stochastic,
            "seed": self.seed,
            "action_meanings": self.action_meanings(),
        }

    def action_meanings(self):
        return {index: f"{kind}:{subject or 'all'}" for index, (kind, subject) in self.ACTIONS.items()}

    def step(self, action):
        if self.done:
            raise RuntimeError("Cannot call step() on a finished episode. Call reset() first.")
        if action not in self.ACTIONS:
            raise ValueError(f"Invalid action {action}. Valid actions: {sorted(self.ACTIONS)}")

        action_type, subject = self.ACTIONS[action]
        prev_mastery = deepcopy(self.mastery)
        prev_energy = self.energy
        info = {
            "action": {"id": action, "type": action_type, "subject": subject},
            "day_finished": False,
        }

        if action_type == "rest":
            self.energy = min(self.max_energy, self.energy + 3.5)
        elif action_type == "study":
            self._apply_study(subject)
        elif action_type == "revise":
            self._apply_revision(subject)

        self.slot += 1
        day_boundary = self.slot >= 3
        if day_boundary:
            self._end_day()
            info["day_finished"] = True

        reward, reward_breakdown = self._compute_reward(prev_mastery, prev_energy, action_type, subject)
        info["reward_breakdown"] = reward_breakdown
        info["performance"] = round(sum(self.mastery.values()) / len(self.mastery), 4)
        info["balance_gap"] = round(max(self.mastery.values()) - min(self.mastery.values()), 4)
        info["history_length"] = len(self.history)

        if self.day > self.max_days:
            self.done = True
            info["episode_summary"] = self._episode_summary()

        self.history.append(
            {
                "day": min(self.day, self.max_days),
                "slot": self.slot if not info["day_finished"] else 0,
                "action": action_type,
                "subject": subject,
                "reward": reward,
            }
        )

        return self.state(), reward, self.done, info

    def _apply_study(self, subject):
        base_gain = 0.18
        difficulty_penalty = 0.06 if self.mastery[subject] > 0.75 else 0.0
        energy_factor = 0.5 + (self.energy / self.max_energy) * 0.5
        gain = max(0.04, base_gain * energy_factor - difficulty_penalty)
        if self.stochastic:
            gain += self.rng.uniform(-0.03, 0.03)
            gain = max(0.02, gain)
        self.mastery[subject] = min(1.0, self.mastery[subject] + gain)
        self.energy = max(0.0, self.energy - 3.0)

    def _apply_revision(self, subject):
        reinforcement = 0.08 + max(0.0, 0.03 - abs(0.6 - self.mastery[subject]) * 0.03)
        if self.stochastic:
            reinforcement += self.rng.uniform(-0.02, 0.02)
            reinforcement = max(0.03, reinforcement)
        self.mastery[subject] = min(1.0, self.mastery[subject] + reinforcement)
        for other in self.SUBJECTS:
            if other != subject:
                support_gain = 0.015
                if self.stochastic:
                    support_gain += self.rng.uniform(-0.005, 0.005)
                    support_gain = max(0.0, support_gain)
                self.mastery[other] = min(1.0, self.mastery[other] + support_gain)
        self.energy = max(0.0, self.energy - 1.5)

    def _end_day(self):
        total_mastery = sum(self.mastery.values())
        if total_mastery < self.daily_target:
            shortfall = self.daily_target - total_mastery
            self.energy = max(0.0, self.energy - shortfall * 0.3)
        self.energy = min(self.max_energy, self.energy + 4.0)
        self.slot = 0
        self.day += 1

    def _compute_reward(self, prev_mastery, prev_energy, action_type, subject):
        current_avg = sum(self.mastery.values()) / len(self.mastery)
        previous_avg = sum(prev_mastery.values()) / len(prev_mastery)
        avg_gain = (current_avg - previous_avg) * 10.0

        balance_gap = max(self.mastery.values()) - min(self.mastery.values())
        previous_gap = max(prev_mastery.values()) - min(prev_mastery.values())
        balance_shift = (previous_gap - balance_gap) * 4.0
        imbalance_penalty = balance_gap * 2.5

        energy_spent = max(0.0, prev_energy - self.energy)
        productivity_gain = sum(self.mastery[name] - prev_mastery[name] for name in self.SUBJECTS)
        energy_efficiency = productivity_gain / (energy_spent + 1.0)
        efficiency_score = energy_efficiency * 5.0

        low_energy_penalty = 0.0
        if self.energy < 2.0 and action_type != "rest":
            low_energy_penalty = 1.5

        targeted_support_bonus = 0.0
        if subject is not None:
            weakest = min(prev_mastery, key=prev_mastery.get)
            if weakest == subject:
                targeted_support_bonus = 0.8

        rest_penalty = 0.2 if action_type == "rest" and prev_energy > self.max_energy * 0.75 else 0.0

        reward = (
            avg_gain
            + balance_shift
            + efficiency_score
            + targeted_support_bonus
            - imbalance_penalty
            - low_energy_penalty
            - rest_penalty
        )
        reward = round(reward, 4)

        breakdown = {
            "average_performance": round(avg_gain, 4),
            "balance_adjustment": round(balance_shift, 4),
            "energy_efficiency": round(efficiency_score, 4),
            "targeted_support_bonus": round(targeted_support_bonus, 4),
            "imbalance_penalty": round(-imbalance_penalty, 4),
            "low_energy_penalty": round(-low_energy_penalty, 4),
            "rest_penalty": round(-rest_penalty, 4),
        }
        return reward, breakdown

    def _episode_summary(self):
        average = sum(self.mastery.values()) / len(self.mastery)
        return {
            "final_mastery": {name: round(value, 4) for name, value in self.mastery.items()},
            "average_mastery": round(average, 4),
            "balance_gap": round(max(self.mastery.values()) - min(self.mastery.values()), 4),
            "energy_left": round(self.energy, 4),
            "days_completed": self.max_days,
        }
