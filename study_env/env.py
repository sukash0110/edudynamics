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
        self.decay_rate = float(self.config.get("decay_rate", 0.012))
        self.consolidation_rate = float(self.config.get("consolidation_rate", 0.028))
        self.spacing_target = int(self.config.get("spacing_target", 2))
        self.energy = float(self.max_energy)
        self.mastery = deepcopy(self.config["initial_mastery"])
        if self.stochastic:
            for subject in self.SUBJECTS:
                offset = self.rng.uniform(-0.05, 0.05)
                self.mastery[subject] = min(1.0, max(0.0, self.mastery[subject] + offset))
        self.memory_strength = {
            subject: min(1.0, max(0.05, self.mastery[subject] * 0.88 + 0.12))
            for subject in self.SUBJECTS
        }
        self.last_touched_day = {subject: 0 for subject in self.SUBJECTS}
        self.days_since_review = {subject: 1 for subject in self.SUBJECTS}
        self.cognitive_load = 0.12
        self.recovery_score = 0.62
        self.last_subject = None
        self.subject_streak = 0
        self.touched_today = set()
        self.history = []
        self.done = False
        return self.state()

    def state(self):
        display_day = min(self.day, self.max_days)
        avg_mastery = sum(self.mastery.values()) / len(self.mastery)
        imbalance = max(self.mastery.values()) - min(self.mastery.values())
        remaining_days = max(0, self.max_days - display_day)
        retention_risk = self._retention_risk_map()
        return {
            "task": self.task_name,
            "day": display_day,
            "slot": self.slot,
            "remaining_days": remaining_days,
            "energy": round(self.energy, 4),
            "energy_ratio": round(self.energy / self.max_energy, 4),
            "mastery": {name: round(value, 4) for name, value in self.mastery.items()},
            "memory_strength": {name: round(value, 4) for name, value in self.memory_strength.items()},
            "retention_risk": {name: round(value, 4) for name, value in retention_risk.items()},
            "avg_mastery": round(avg_mastery, 4),
            "imbalance": round(imbalance, 4),
            "daily_target": self.daily_target,
            "cognitive_load": round(self.cognitive_load, 4),
            "recovery_score": round(self.recovery_score, 4),
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
        prev_memory = deepcopy(self.memory_strength)
        prev_energy = self.energy
        prev_load = self.cognitive_load
        info = {
            "action": {"id": action, "type": action_type, "subject": subject},
            "day_finished": False,
        }

        spacing_alignment = 0.0
        repetition_penalty = 0.0

        if action_type == "rest":
            self.energy = min(self.max_energy, self.energy + 3.5)
            self.cognitive_load = max(0.0, self.cognitive_load - 0.22)
            self.recovery_score = min(1.0, self.recovery_score + 0.16)
        elif action_type == "study":
            spacing_alignment, repetition_penalty = self._apply_study(subject)
        elif action_type == "revise":
            spacing_alignment, repetition_penalty = self._apply_revision(subject)

        self.slot += 1
        day_boundary = self.slot >= 3
        if day_boundary:
            self._end_day()
            info["day_finished"] = True

        reward, reward_breakdown = self._compute_reward(
            prev_mastery,
            prev_memory,
            prev_energy,
            prev_load,
            action_type,
            subject,
            spacing_alignment,
            repetition_penalty,
        )
        info["reward_breakdown"] = reward_breakdown
        info["performance"] = round(sum(self.mastery.values()) / len(self.mastery), 4)
        info["balance_gap"] = round(max(self.mastery.values()) - min(self.mastery.values()), 4)
        info["retention_risk"] = {name: round(value, 4) for name, value in self._retention_risk_map().items()}
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
        spacing_bonus, repetition_penalty = self._learning_modifiers(subject)
        base_gain = 0.18
        difficulty_penalty = 0.06 if self.mastery[subject] > 0.75 else 0.0
        energy_factor = 0.48 + (self.energy / self.max_energy) * 0.52
        load_factor = max(0.45, 1.0 - self.cognitive_load * 0.4)
        retention_factor = 1.0 + max(0.0, 0.55 - self.memory_strength[subject]) * 0.2
        gain = max(0.035, base_gain * energy_factor * load_factor * retention_factor + spacing_bonus - difficulty_penalty - repetition_penalty)
        if self.stochastic:
            gain += self.rng.uniform(-0.03, 0.03)
            gain = max(0.02, gain)
        self.mastery[subject] = min(1.0, self.mastery[subject] + gain)
        memory_gain = 0.045 + spacing_bonus * 0.85 - repetition_penalty * 0.5
        self.memory_strength[subject] = min(1.0, self.memory_strength[subject] + max(0.015, memory_gain))
        self.energy = max(0.0, self.energy - (2.7 + self.cognitive_load * 0.5))
        self.cognitive_load = min(1.0, self.cognitive_load + 0.17 + repetition_penalty * 0.9)
        self.recovery_score = max(0.0, self.recovery_score - 0.09)
        self._mark_subject_touch(subject)
        return spacing_bonus, repetition_penalty

    def _apply_revision(self, subject):
        spacing_bonus, repetition_penalty = self._learning_modifiers(subject)
        reinforcement = 0.08 + max(0.0, 0.03 - abs(0.6 - self.mastery[subject]) * 0.03) + spacing_bonus * 0.75
        if self.stochastic:
            reinforcement += self.rng.uniform(-0.02, 0.02)
            reinforcement = max(0.03, reinforcement)
        self.mastery[subject] = min(1.0, self.mastery[subject] + reinforcement)
        self.memory_strength[subject] = min(1.0, self.memory_strength[subject] + 0.085 + spacing_bonus - repetition_penalty * 0.35)
        for other in self.SUBJECTS:
            if other != subject:
                support_gain = 0.012 + spacing_bonus * 0.15
                if self.stochastic:
                    support_gain += self.rng.uniform(-0.005, 0.005)
                    support_gain = max(0.0, support_gain)
                self.mastery[other] = min(1.0, self.mastery[other] + support_gain)
                self.memory_strength[other] = min(1.0, self.memory_strength[other] + support_gain * 0.35)
        self.energy = max(0.0, self.energy - (1.35 + self.cognitive_load * 0.28))
        self.cognitive_load = min(1.0, self.cognitive_load + 0.1 + repetition_penalty * 0.5)
        self.recovery_score = max(0.0, self.recovery_score - 0.05)
        self._mark_subject_touch(subject)
        return spacing_bonus, repetition_penalty

    def _mark_subject_touch(self, subject):
        if self.last_subject == subject:
            self.subject_streak += 1
        else:
            self.last_subject = subject
            self.subject_streak = 1
        self.touched_today.add(subject)
        self.days_since_review[subject] = 0
        self.last_touched_day[subject] = self.day

    def _learning_modifiers(self, subject):
        spacing_gap = self.days_since_review.get(subject, self.day - self.last_touched_day.get(subject, 0))
        alignment = 1.0 - min(1.0, abs(spacing_gap - self.spacing_target) / max(self.spacing_target, 1))
        spacing_bonus = 0.012 + alignment * 0.038
        repetition_penalty = 0.018 * max(0, self.subject_streak - 1) if self.last_subject == subject else 0.0
        if spacing_gap == 0:
            spacing_bonus *= 0.4
        return spacing_bonus, repetition_penalty

    def _retention_risk_map(self):
        risks = {}
        for subject in self.SUBJECTS:
            spacing_gap = self.days_since_review.get(subject, self.day - self.last_touched_day.get(subject, 0))
            gap_pressure = min(1.0, spacing_gap / (self.spacing_target + 2))
            risks[subject] = min(1.0, max(0.0, gap_pressure * 0.6 + (1.0 - self.memory_strength[subject]) * 0.4))
        return risks

    def _end_day(self):
        total_mastery = sum(self.mastery.values())
        if total_mastery < self.daily_target:
            shortfall = self.daily_target - total_mastery
            self.energy = max(0.0, self.energy - shortfall * 0.3)
        retention_risk = self._retention_risk_map()
        for subject in self.SUBJECTS:
            if subject not in self.touched_today:
                decay = self.decay_rate * (0.55 + retention_risk[subject]) * (1.0 - self.memory_strength[subject] * 0.5)
                self.mastery[subject] = max(0.0, self.mastery[subject] - decay)
                self.memory_strength[subject] = max(0.02, self.memory_strength[subject] - decay * 0.85)
            else:
                consolidation = self.consolidation_rate * (0.7 + self.recovery_score * 0.4)
                self.memory_strength[subject] = min(1.0, self.memory_strength[subject] + consolidation)
                self.mastery[subject] = min(1.0, self.mastery[subject] + consolidation * 0.35)
            self.days_since_review[subject] = self.days_since_review.get(subject, 0) + 1
        self.energy = min(self.max_energy, self.energy + 4.0)
        self.cognitive_load = max(0.04, self.cognitive_load * 0.62)
        self.recovery_score = min(1.0, self.recovery_score + 0.12)
        self.touched_today = set()
        self.slot = 0
        self.day += 1

    def _compute_reward(self, prev_mastery, prev_memory, prev_energy, prev_load, action_type, subject, spacing_alignment, repetition_penalty):
        current_avg = sum(self.mastery.values()) / len(self.mastery)
        previous_avg = sum(prev_mastery.values()) / len(prev_mastery)
        avg_gain = (current_avg - previous_avg) * 10.0

        current_memory = sum(self.memory_strength.values()) / len(self.memory_strength)
        previous_memory = sum(prev_memory.values()) / len(prev_memory)
        retention_gain = (current_memory - previous_memory) * 6.0

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
        spacing_reward = spacing_alignment * 0.9 if action_type != "rest" else 0.0
        cram_penalty = repetition_penalty * 9.0
        load_regulation = max(0.0, prev_load - self.cognitive_load) * 2.0 if action_type == "rest" else -max(0.0, self.cognitive_load - prev_load) * 0.6

        reward = (
            avg_gain
            + retention_gain
            + balance_shift
            + efficiency_score
            + spacing_reward
            + load_regulation
            + targeted_support_bonus
            - imbalance_penalty
            - low_energy_penalty
            - rest_penalty
            - cram_penalty
        )
        reward = round(reward, 4)

        breakdown = {
            "average_performance": round(avg_gain, 4),
            "retention_progress": round(retention_gain, 4),
            "balance_adjustment": round(balance_shift, 4),
            "energy_efficiency": round(efficiency_score, 4),
            "spacing_reward": round(spacing_reward, 4),
            "load_regulation": round(load_regulation, 4),
            "targeted_support_bonus": round(targeted_support_bonus, 4),
            "imbalance_penalty": round(-imbalance_penalty, 4),
            "low_energy_penalty": round(-low_energy_penalty, 4),
            "rest_penalty": round(-rest_penalty, 4),
            "cram_penalty": round(-cram_penalty, 4),
        }
        return reward, breakdown

    def _episode_summary(self):
        average = sum(self.mastery.values()) / len(self.mastery)
        average_memory = sum(self.memory_strength.values()) / len(self.memory_strength)
        return {
            "final_mastery": {name: round(value, 4) for name, value in self.mastery.items()},
            "final_memory_strength": {name: round(value, 4) for name, value in self.memory_strength.items()},
            "average_mastery": round(average, 4),
            "average_memory_strength": round(average_memory, 4),
            "balance_gap": round(max(self.mastery.values()) - min(self.mastery.values()), 4),
            "energy_left": round(self.energy, 4),
            "cognitive_load": round(self.cognitive_load, 4),
            "recovery_score": round(self.recovery_score, 4),
            "days_completed": self.max_days,
        }
