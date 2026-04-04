import base64
from datetime import datetime
from pathlib import Path

import streamlit as st

from evaluation.grader_runner import evaluate_task
from runtime.inference_runner import run_episode
from study_env.env import StudyPlannerEnv
from study_env.tasks import TASKS


APP_NAME = "EduDynamics"
APP_VERSION = "1.1.1"
UI_LAYER_NAME = "AuraUI"
UI_LAYER_VERSION = "1.1.1"
LOGO_PATH = str(Path(__file__).resolve().parent / "assets" / "edudynamics-logo.svg")
SUBJECT_COLORS = {
    "math": "#64d2ff",
    "physics": "#7d7aff",
    "chemistry": "#9cf28f",
}
ACTION_LABELS = {
    0: "Study Math",
    1: "Study Physics",
    2: "Study Chemistry",
    3: "Revise Math",
    4: "Revise Physics",
    5: "Revise Chemistry",
    6: "Rest",
}


def inject_styles(appearance="dark"):
    if appearance == "light":
        css = """
        <style>
        :root {
            --glass-bg: rgba(255, 255, 255, 0.76);
            --glass-border: rgba(173, 190, 214, 0.5);
            --glass-shadow: 0 24px 56px rgba(96, 121, 150, 0.18);
            --text-main: #11233b;
            --text-soft: rgba(39, 59, 84, 0.82);
            --text-faint: rgba(82, 104, 132, 0.82);
            --sidebar-bg: linear-gradient(180deg, rgba(244, 249, 255, 0.92), rgba(227, 237, 252, 0.88));
            --control-bg: rgba(255, 255, 255, 0.92);
            --control-border: rgba(122, 146, 173, 0.28);
            --button-bg: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(233,241,255,0.8));
            --tab-bg: rgba(255,255,255,0.72);
            --tab-selected: linear-gradient(135deg, rgba(100,210,255,0.32), rgba(125,122,255,0.22));
        }
        .stApp {
            background:
                radial-gradient(circle at 14% 18%, rgba(100, 210, 255, 0.34), transparent 22%),
                radial-gradient(circle at 86% 14%, rgba(125, 122, 255, 0.22), transparent 24%),
                radial-gradient(circle at 76% 82%, rgba(156, 242, 143, 0.18), transparent 22%),
                linear-gradient(145deg, #edf4ff 0%, #f5f8ff 36%, #eef7f4 100%);
            color: var(--text-main);
        }
        [data-testid="stHeader"] {
            background: rgba(248, 251, 255, 0.78) !important;
            border-bottom: 1px solid rgba(173, 190, 214, 0.22);
            backdrop-filter: blur(18px);
        }
        [data-testid="stToolbar"] {
            right: 1rem;
            top: 0.5rem;
        }
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2rem;
        }
        [data-testid="stSidebar"] {
            background: var(--sidebar-bg) !important;
            backdrop-filter: blur(30px);
            border-right: 1px solid var(--glass-border);
        }
        [data-testid="stSidebar"] * {
            color: var(--text-main);
        }
        [data-testid="stSidebar"] .stCaption,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stMarkdown p {
            color: var(--text-soft) !important;
        }
        [data-testid="stSidebar"] .stSelectbox > div > div,
        [data-testid="stSidebar"] .stNumberInput > div > div > input {
            background: var(--control-bg) !important;
            color: var(--text-main) !important;
            border: 1px solid var(--control-border) !important;
            border-radius: 18px !important;
        }
        [data-testid="stSidebar"] .stNumberInput button,
        [data-testid="stSidebar"] .stSelectbox button {
            background: rgba(255, 255, 255, 0.72) !important;
            color: #16304a !important;
            border: 1px solid rgba(122, 146, 173, 0.22) !important;
        }
        .stSelectbox > div > div,
        .stNumberInput > div > div > input,
        .stTextInput > div > div > input {
            color: var(--text-main) !important;
        }
        .stNumberInput input {
            background: rgba(255, 255, 255, 0.9) !important;
            color: #11233b !important;
        }
        .stRadio [role="radiogroup"] label {
            color: #17324f !important;
        }
        .stButton button {
            border-radius: 999px !important;
            border: 1px solid var(--control-border) !important;
            background: var(--button-bg) !important;
            color: var(--text-main) !important;
            box-shadow: 0 12px 26px rgba(5, 10, 20, 0.12);
        }
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, rgba(100,210,255,0.84), rgba(125,122,255,0.72)) !important;
            color: #07111f !important;
        }
        .hero {
            border: 1px solid var(--glass-border);
            background:
                linear-gradient(135deg, rgba(255,255,255,0.86), rgba(248,251,255,0.72)),
                radial-gradient(circle at top right, rgba(116, 219, 255, 0.18), transparent 42%);
            backdrop-filter: blur(34px);
            border-radius: 32px;
            padding: 1.7rem 1.8rem;
            box-shadow: var(--glass-shadow);
            margin-bottom: 1rem;
        }
        .hero-kicker {
            color: #1477a6;
            font-size: 0.84rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.4rem;
        }
        .hero-title, .big-number {
            color: #0f2037;
        }
        .hero-title {
            font-size: 2.2rem;
            line-height: 1.05;
            font-weight: 800;
            margin-bottom: 0.55rem;
        }
        .hero-copy, .support-text {
            color: var(--text-soft);
        }
        .hero-copy {
            font-size: 1rem;
            line-height: 1.55;
            max-width: 50rem;
        }
        .panel {
            border: 1px solid var(--glass-border);
            background: linear-gradient(180deg, rgba(255,255,255,0.82), rgba(246,250,255,0.72));
            backdrop-filter: blur(28px);
            border-radius: 24px;
            padding: 1.1rem 1.2rem;
            box-shadow: var(--glass-shadow);
        }
        .mini-label {
            color: var(--text-faint);
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        .big-number {
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.1;
            margin-top: 0.35rem;
        }
        .subject-card {
            border-radius: 24px;
            padding: 1rem;
            color: white;
            min-height: 144px;
            box-shadow: 0 18px 38px rgba(8, 15, 28, 0.18);
            border: 1px solid rgba(255,255,255,0.35);
            backdrop-filter: blur(22px);
        }
        .subject-name {
            font-size: 0.82rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 700;
            opacity: 0.92;
        }
        .subject-value {
            font-size: 2rem;
            font-weight: 800;
            margin-top: 0.25rem;
        }
        .subject-caption, .subject-detail {
            font-size: 0.9rem;
            opacity: 0.92;
            margin-top: 0.32rem;
        }
        .logo-shell {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 14px;
            border-radius: 26px;
            background: linear-gradient(160deg, rgba(255, 255, 255, 0.98), rgba(232, 241, 255, 0.82));
            box-shadow: 0 18px 42px rgba(8, 15, 28, 0.14);
            border: 1px solid rgba(139, 168, 199, 0.32);
        }
        .glass-note {
            border: 1px solid rgba(139, 168, 199, 0.24);
            background: linear-gradient(180deg, rgba(255,255,255,0.82), rgba(246,250,255,0.72));
            backdrop-filter: blur(22px);
            border-radius: 22px;
            padding: 1rem 1.1rem;
            color: var(--text-soft);
            box-shadow: 0 16px 34px rgba(8, 15, 28, 0.12);
        }
        .glass-note code {
            background: rgba(16, 34, 56, 0.08);
            color: #16304a;
            border-radius: 8px;
            padding: 0.08rem 0.4rem;
        }
        .review-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.38rem 0.82rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            border: 1px solid transparent;
            margin-bottom: 0.7rem;
        }
        .review-badge.excellent {
            background: rgba(20, 184, 116, 0.16);
            color: #0e8f5b;
            border-color: rgba(20, 184, 116, 0.22);
        }
        .review-badge.on-target {
            background: rgba(14, 165, 233, 0.16);
            color: #0c7fb0;
            border-color: rgba(14, 165, 233, 0.22);
        }
        .review-badge.borderline {
            background: rgba(245, 158, 11, 0.16);
            color: #b46808;
            border-color: rgba(245, 158, 11, 0.22);
        }
        .review-badge.needs-attention {
            background: rgba(239, 68, 68, 0.14);
            color: #c43d3d;
            border-color: rgba(239, 68, 68, 0.2);
        }
        .review-history {
            display: grid;
            gap: 0.8rem;
        }
        .review-history-item {
            border: 1px solid var(--glass-border);
            background: linear-gradient(180deg, rgba(255,255,255,0.82), rgba(246,250,255,0.72));
            border-radius: 20px;
            padding: 0.95rem 1rem;
            box-shadow: 0 12px 26px rgba(8, 15, 28, 0.08);
        }
        .review-history-meta {
            color: var(--text-faint);
            font-size: 0.8rem;
            margin-top: 0.45rem;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.65rem;
        }
        .stTabs [data-baseweb="tab"] {
            background: var(--tab-bg);
            border: 1px solid var(--control-border);
            border-radius: 999px;
            color: var(--text-main);
            padding: 0.55rem 1rem;
        }
        .stTabs [aria-selected="true"] {
            background: var(--tab-selected);
        }
        .stInfo {
            background: rgba(188, 220, 255, 0.5) !important;
            color: #14304d !important;
            border: 1px solid rgba(120, 168, 220, 0.24) !important;
        }
        </style>
        """
    else:
        css = """
        <style>
        :root {
            --glass-bg: rgba(255, 255, 255, 0.12);
            --glass-border: rgba(255, 255, 255, 0.22);
            --glass-shadow: 0 28px 72px rgba(8, 15, 28, 0.28);
            --text-main: #f8fbff;
            --text-soft: rgba(233, 242, 255, 0.82);
            --text-faint: rgba(216, 229, 247, 0.7);
            --sidebar-bg: linear-gradient(180deg, rgba(8, 15, 28, 0.76), rgba(17, 28, 46, 0.66));
            --control-bg: rgba(11, 21, 36, 0.6);
            --control-border: rgba(255, 255, 255, 0.12);
            --button-bg: linear-gradient(180deg, rgba(255,255,255,0.22), rgba(255,255,255,0.08));
            --tab-bg: rgba(255,255,255,0.08);
            --tab-selected: linear-gradient(135deg, rgba(100,210,255,0.22), rgba(125,122,255,0.2));
        }
        .stApp {
            background:
                radial-gradient(circle at 15% 18%, rgba(100, 210, 255, 0.42), transparent 24%),
                radial-gradient(circle at 84% 14%, rgba(125, 122, 255, 0.35), transparent 26%),
                radial-gradient(circle at 78% 82%, rgba(156, 242, 143, 0.24), transparent 22%),
                linear-gradient(145deg, #07101b 0%, #142338 38%, #1b2d48 100%);
            color: var(--text-main);
        }
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2rem;
        }
        [data-testid="stSidebar"] {
            background: var(--sidebar-bg) !important;
            backdrop-filter: blur(30px);
            border-right: 1px solid var(--glass-border);
        }
        [data-testid="stSidebar"] * {
            color: var(--text-main);
        }
        [data-testid="stSidebar"] .stCaption,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stMarkdown p {
            color: var(--text-soft) !important;
        }
        [data-testid="stSidebar"] .stSelectbox > div > div,
        [data-testid="stSidebar"] .stNumberInput > div > div > input {
            background: var(--control-bg) !important;
            color: var(--text-main) !important;
            border: 1px solid var(--control-border) !important;
            border-radius: 18px !important;
        }
        .stSelectbox > div > div,
        .stNumberInput > div > div > input,
        .stTextInput > div > div > input {
            color: var(--text-main) !important;
        }
        .stRadio label,
        .stCheckbox label,
        .stMarkdown,
        .stAlert,
        .stMetric,
        [data-testid="stDataFrame"] {
            color: var(--text-main);
        }
        .stButton button {
            border-radius: 999px !important;
            border: 1px solid var(--control-border) !important;
            background: var(--button-bg) !important;
            color: var(--text-main) !important;
            box-shadow: 0 12px 26px rgba(5, 10, 20, 0.24);
        }
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, rgba(100,210,255,0.84), rgba(125,122,255,0.82)) !important;
            color: #07111f !important;
        }
        .hero {
            border: 1px solid var(--glass-border);
            background:
                linear-gradient(135deg, rgba(255,255,255,0.16), rgba(255,255,255,0.06)),
                radial-gradient(circle at top right, rgba(116, 219, 255, 0.18), transparent 42%);
            backdrop-filter: blur(34px);
            border-radius: 32px;
            padding: 1.7rem 1.8rem;
            box-shadow: var(--glass-shadow);
            margin-bottom: 1rem;
        }
        .hero-kicker {
            color: #9fe7ff;
            font-size: 0.84rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.4rem;
        }
        .hero-title {
            color: #ffffff;
            font-size: 2.2rem;
            line-height: 1.05;
            font-weight: 800;
            margin-bottom: 0.55rem;
        }
        .hero-copy {
            color: var(--text-soft);
            font-size: 1rem;
            line-height: 1.55;
            max-width: 50rem;
        }
        .panel {
            border: 1px solid var(--glass-border);
            background: var(--glass-bg);
            backdrop-filter: blur(28px);
            border-radius: 24px;
            padding: 1.1rem 1.2rem;
            box-shadow: var(--glass-shadow);
        }
        .mini-label {
            color: var(--text-faint);
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        .big-number {
            color: #ffffff;
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.1;
            margin-top: 0.35rem;
        }
        .support-text {
            color: var(--text-soft);
            font-size: 0.92rem;
            margin-top: 0.25rem;
        }
        .subject-card {
            border-radius: 24px;
            padding: 1rem;
            color: white;
            min-height: 144px;
            box-shadow: 0 18px 38px rgba(8, 15, 28, 0.26);
            border: 1px solid rgba(255,255,255,0.2);
            backdrop-filter: blur(22px);
        }
        .subject-name {
            font-size: 0.82rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 700;
            opacity: 0.92;
        }
        .subject-value {
            font-size: 2rem;
            font-weight: 800;
            margin-top: 0.25rem;
        }
        .subject-caption, .subject-detail {
            font-size: 0.9rem;
            opacity: 0.9;
            margin-top: 0.32rem;
        }
        .logo-shell {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 14px;
            border-radius: 26px;
            background: linear-gradient(160deg, rgba(255, 255, 255, 0.9), rgba(222, 236, 255, 0.5));
            box-shadow: 0 18px 42px rgba(8, 15, 28, 0.34);
            border: 1px solid rgba(255, 255, 255, 0.34);
        }
        .glass-note {
            border: 1px solid rgba(255,255,255,0.16);
            background: linear-gradient(180deg, rgba(255,255,255,0.12), rgba(255,255,255,0.05));
            backdrop-filter: blur(22px);
            border-radius: 22px;
            padding: 1rem 1.1rem;
            color: var(--text-soft);
            box-shadow: 0 16px 34px rgba(8, 15, 28, 0.24);
        }
        .review-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.38rem 0.82rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            border: 1px solid transparent;
            margin-bottom: 0.7rem;
        }
        .review-badge.excellent {
            background: rgba(52, 211, 153, 0.18);
            color: #b8ffe2;
            border-color: rgba(52, 211, 153, 0.26);
        }
        .review-badge.on-target {
            background: rgba(56, 189, 248, 0.18);
            color: #c8f2ff;
            border-color: rgba(56, 189, 248, 0.26);
        }
        .review-badge.borderline {
            background: rgba(251, 191, 36, 0.18);
            color: #ffe8ad;
            border-color: rgba(251, 191, 36, 0.24);
        }
        .review-badge.needs-attention {
            background: rgba(248, 113, 113, 0.18);
            color: #ffd4d4;
            border-color: rgba(248, 113, 113, 0.24);
        }
        .review-history {
            display: grid;
            gap: 0.8rem;
        }
        .review-history-item {
            border: 1px solid var(--glass-border);
            background: linear-gradient(180deg, rgba(255,255,255,0.14), rgba(255,255,255,0.06));
            border-radius: 20px;
            padding: 0.95rem 1rem;
            box-shadow: 0 14px 30px rgba(8, 15, 28, 0.18);
        }
        .review-history-meta {
            color: var(--text-faint);
            font-size: 0.8rem;
            margin-top: 0.45rem;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.65rem;
        }
        .stTabs [data-baseweb="tab"] {
            background: var(--tab-bg);
            border: 1px solid var(--control-border);
            border-radius: 999px;
            color: var(--text-main);
            padding: 0.55rem 1rem;
        }
        .stTabs [aria-selected="true"] {
            background: var(--tab-selected);
        }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


def build_trace_rows(trace):
    rows = []
    for item in trace:
        action = item["action"]
        rows.append(
            {
                "step": item["step"],
                "day": item["day"],
                "energy": item["energy"],
                "avg_mastery": item["avg_mastery"],
                "imbalance": item["imbalance"],
                "cognitive_load": item.get("cognitive_load", 0.0),
                "recovery_score": item.get("recovery_score", 0.0),
                "reward": item["reward"],
                "action_type": action["type"],
                "subject": action["subject"] or "all",
            }
        )
    return rows


def build_reward_rows(trace):
    rows = []
    for item in trace:
        row = {"step": item["step"]}
        row.update(item.get("reward_breakdown", {}))
        rows.append(row)
    return rows


def build_subject_rows(trace):
    rows = []
    for item in trace:
        row = {"step": item["step"]}
        row.update(item.get("mastery", {}))
        rows.append(row)
    return rows


def build_memory_rows(trace):
    rows = []
    for item in trace:
        row = {"step": item["step"]}
        row.update(item.get("memory_strength", {}))
        rows.append(row)
    return rows


def build_retention_rows(trace):
    rows = []
    for item in trace:
        row = {"step": item["step"]}
        row.update(item.get("retention_risk", {}))
        rows.append(row)
    return rows


@st.cache_data(show_spinner=False)
def run_episode_cached(task_name, stochastic, seed, agent_mode):
    return run_episode(task_name, stochastic=stochastic, seed=seed, agent_mode=agent_mode)


def safe_has_openai_key():
    try:
        if st.secrets.get("OPENAI_API_KEY"):
            return True
    except Exception:
        pass
    return bool(st.session_state.get("has_openai_key") or st.session_state.get("openai_key_hint"))


def _aggregate_reward_components(trace):
    totals = {}
    for item in trace:
        for component, value in item.get("reward_breakdown", {}).items():
            totals[component] = totals.get(component, 0.0) + value
    return {key: round(value, 4) for key, value in totals.items()}


def build_run_review(summary):
    evaluation = evaluate_task(summary["task"], summary)
    metrics = evaluation["metrics"]
    thresholds = evaluation["thresholds"]
    reward_ratio = metrics["total_reward"] / max(thresholds["min_reward"], 0.0001)
    reward_delta = round(metrics["total_reward"] - thresholds["min_reward"], 4)
    components = _aggregate_reward_components(summary["trace"])
    best_component = max(components.items(), key=lambda item: item[1], default=("none", 0.0))
    biggest_drag = min(components.items(), key=lambda item: item[1], default=("none", 0.0))

    if reward_ratio >= 1.15:
        verdict = "Excellent"
        tone = "This run is beating the reward target comfortably."
    elif reward_ratio >= 1.0:
        verdict = "On target"
        tone = "This run clears the reward target and is in a healthy range."
    elif reward_ratio >= 0.8:
        verdict = "Borderline"
        tone = "This run is close, but the reward leaves room for a tighter study plan."
    else:
        verdict = "Needs attention"
        tone = "This run is under the reward target and needs a better pacing strategy."

    feedback = []
    if reward_delta >= 0:
        feedback.append(f"Reward finished {reward_delta:.2f} above the {summary['task']} target.")
    else:
        feedback.append(f"Reward finished {abs(reward_delta):.2f} below the {summary['task']} target.")

    if not evaluation["checks"]["mastery_ok"]:
        feedback.append("Mastery is still lagging, so bias the next run toward weaker subjects before spending actions on maintenance.")
    if not evaluation["checks"]["balance_ok"]:
        feedback.append("Subject balance drifted too far, so rotate earlier into the neglected subject to protect the composite reward.")
    if metrics["energy_left"] <= 0.2:
        feedback.append("Energy ended low, which usually means the run needs an earlier rest or revision pivot instead of one more intensive study block.")
    if biggest_drag[1] < 0:
        feedback.append(f"The largest reward drag was `{biggest_drag[0]}` at {biggest_drag[1]:.2f}, so that is the first place to tighten the policy.")
    if best_component[1] > 0:
        feedback.append(f"The strongest contributor was `{best_component[0]}` at +{best_component[1]:.2f}; keep that pattern in the next run.")
    if len(feedback) < 3:
        feedback.append("The reward profile is stable enough to reuse this sequence as a baseline and compare future stochastic runs against it.")

    return {
        "verdict": verdict,
        "badge_class": verdict.lower().replace(" ", "-"),
        "tone": tone,
        "score": evaluation["score"],
        "reward_target": thresholds["min_reward"],
        "reward_delta": reward_delta,
        "feedback": " ".join(feedback[:4]),
        "components": components,
    }


def render_logo(width_px, framed=False):
    svg_text = Path(LOGO_PATH).read_text(encoding="utf-8")
    encoded = base64.b64encode(svg_text.encode("utf-8")).decode("utf-8")
    wrapper_class = "logo-shell" if framed else ""
    st.markdown(
        f"""
        <div style="display:flex; justify-content:center;">
            <div class="{wrapper_class}">
                <img src="data:image/svg+xml;base64,{encoded}" width="{width_px}" alt="{APP_NAME} logo" />
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero():
    logo_col, copy_col = st.columns([0.95, 3.05], vertical_alignment="center")
    with logo_col:
        render_logo(260)
    with copy_col:
        st.markdown(
            f"""
            <div class="hero">
                <div class="hero-kicker">{UI_LAYER_NAME} {UI_LAYER_VERSION}</div>
                <div class="hero-title">A liquid-glass command center for real study momentum.</div>
                <div class="hero-copy">
                    Explore manual interventions, richer reward telemetry, retention risk, and memory strength as the planner balances focus, recovery, spacing, and subject coverage.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_metric_panels(summary):
    episode = summary["episode_summary"]
    cards = [
        ("Total Reward", summary["total_reward"], "Composite score across progress, retention, spacing, and recovery."),
        ("Average Mastery", episode.get("average_mastery"), "Final skill level averaged across all three subjects."),
        ("Memory Strength", episode.get("average_memory_strength"), "How durable the learned material is after consolidation."),
        ("Balance Gap", episode.get("balance_gap"), "Lower is better. Zero means balanced study coverage."),
        ("Recovery", episode.get("recovery_score"), "Readiness preserved through rest and sustainable pacing."),
    ]
    columns = st.columns(len(cards))
    for column, (label, value, copy) in zip(columns, cards):
        column.markdown(
            f"""
            <div class="panel">
                <div class="mini-label">{label}</div>
                <div class="big-number">{value}</div>
                <div class="support-text">{copy}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_subject_cards(summary):
    mastery = summary["final_state"]["mastery"]
    memory_strength = summary["final_state"].get("memory_strength", {})
    retention_risk = summary["final_state"].get("retention_risk", {})
    avg_mastery = summary["episode_summary"]["average_mastery"]
    cols = st.columns(3)
    for col, subject in zip(cols, ("math", "physics", "chemistry")):
        value = mastery[subject]
        color = SUBJECT_COLORS[subject]
        delta = round(value - avg_mastery, 4)
        caption = "Above plan average" if delta >= 0 else "Below plan average"
        col.markdown(
            f"""
            <div class="subject-card" style="background: linear-gradient(160deg, {color}, rgba(18, 26, 50, 0.88));">
                <div class="subject-name">{subject}</div>
                <div class="subject-value">{value:.4f}</div>
                <div class="subject-caption">{caption}: {delta:+.4f}</div>
                <div class="subject-detail">Memory strength: {memory_strength.get(subject, 0):.4f}</div>
                <div class="subject-detail">Retention risk: {retention_risk.get(subject, 0):.4f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_plan_snapshot(summary):
    final_state = summary["final_state"]
    mode_label = "randomized" if final_state["seed"] is None else ("stochastic" if summary["stochastic"] else "deterministic")
    seed_label = "auto-generated" if final_state["seed"] is None else final_state["seed"]

    left, right = st.columns([1.05, 1.2])
    with left:
        st.markdown("### Run Snapshot")
        st.markdown(
            f"""
            <div class="panel">
                <div class="mini-label">Scenario</div>
                <div class="support-text">
                    Task: <strong>{summary["task"]}</strong><br>
                    Agent: <strong>{summary.get("agent_mode", "heuristic")}</strong><br>
                    Mode: <strong>{mode_label}</strong><br>
                    Seed: <strong>{seed_label}</strong><br>
                    Steps executed: <strong>{summary["steps"]}</strong><br>
                    Final cognitive load: <strong>{summary["episode_summary"].get("cognitive_load", 0)}</strong><br>
                    Final recovery score: <strong>{summary["episode_summary"].get("recovery_score", 0)}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("")
        st.progress(min(final_state["energy_ratio"], 1.0), text=f"Final energy ratio: {final_state['energy_ratio']:.0%}")
        st.progress(
            min(summary["episode_summary"]["average_mastery"], 1.0),
            text=f"Average mastery reached: {summary['episode_summary']['average_mastery']:.0%}",
        )
        st.progress(
            min(summary["episode_summary"].get("average_memory_strength", 0.0), 1.0),
            text=f"Memory durability reached: {summary['episode_summary'].get('average_memory_strength', 0.0):.0%}",
        )
    with right:
        st.markdown("### Reward Design")
        st.markdown(
            f"""
            <div class="panel">
                <div class="support-text">
                    {APP_NAME} visualizes learning that lasts through the {UI_LAYER_NAME} {UI_LAYER_VERSION} layer:
                    <br><br>
                    <strong>Performance</strong> rewards mastery gains.
                    <br>
                    <strong>Retention</strong> rewards stronger memory traces.
                    <br>
                    <strong>Spacing</strong> favors timely revision over cramming.
                    <br>
                    <strong>Recovery</strong> rewards lower load and better pacing.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_run_review(summary):
    review = build_run_review(summary)
    history_rows = st.session_state.get("run_history", [])

    left, right = st.columns([1.15, 1.0])
    with left:
        st.markdown("### Run Review")
        st.markdown(
            f"""
            <div class="panel">
                <div class="review-badge {review["badge_class"]}">{review["verdict"]}</div>
                <div class="big-number">{summary["total_reward"]:.2f}</div>
                <div class="support-text">
                    {review["tone"]}<br><br>
                    Review score: <strong>{review["score"]:.2f}</strong><br>
                    Reward target: <strong>{review["reward_target"]:.2f}</strong><br>
                    Feedback: {review["feedback"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown("### Recent Reviews")
        if history_rows:
            history_markup = "".join(
                f"""
                <div class="review-history-item">
                    <div class="review-badge {item["badge_class"]}">{item["review"]}</div>
                    <div><strong>{item["task"].title()}</strong> · reward <strong>{item["reward"]:.2f}</strong></div>
                    <div class="support-text">{item["feedback"]}</div>
                    <div class="review-history-meta">{item["time"]} · {item["mode"]} · seed {item["seed"]}</div>
                </div>
                """
                for item in history_rows[:6]
            )
            st.markdown(f'<div class="review-history">{history_markup}</div>', unsafe_allow_html=True)
        else:
            st.info("Run a simulation to start collecting reward-based reviews.")


def render_analytics(summary):
    rows = build_trace_rows(summary["trace"])
    reward_rows = build_reward_rows(summary["trace"])
    subject_rows = build_subject_rows(summary["trace"])
    memory_rows = build_memory_rows(summary["trace"])
    retention_rows = build_retention_rows(summary["trace"])

    st.markdown("### Analytics")
    chart_cols = st.columns(3)
    with chart_cols[0]:
        st.markdown("**Energy trajectory**")
        st.line_chart([{"step": row["step"], "energy": row["energy"]} for row in rows], x="step", y="energy")
    with chart_cols[1]:
        st.markdown("**Average mastery**")
        st.line_chart([{"step": row["step"], "avg_mastery": row["avg_mastery"]} for row in rows], x="step", y="avg_mastery")
    with chart_cols[2]:
        st.markdown("**Reward by step**")
        st.bar_chart([{"step": row["step"], "reward": row["reward"]} for row in rows], x="step", y="reward")

    middle_cols = st.columns(2)
    with middle_cols[0]:
        st.markdown("**Reward component breakdown**")
        if reward_rows:
            st.area_chart(reward_rows, x="step")
    with middle_cols[1]:
        st.markdown("**Subject mastery over time**")
        if subject_rows:
            st.line_chart(subject_rows, x="step")

    lower_cols = st.columns(2)
    with lower_cols[0]:
        st.markdown("**Memory strength over time**")
        if memory_rows:
            st.line_chart(memory_rows, x="step")
    with lower_cols[1]:
        st.markdown("**Retention risk over time**")
        if retention_rows:
            st.line_chart(retention_rows, x="step")

    view = st.segmented_control("Trace view", options=["Recent", "Full"], default="Recent", selection_mode="single")
    if view == "Recent":
        st.dataframe(rows[-8:], use_container_width=True, hide_index=True)
    else:
        st.dataframe(rows, use_container_width=True, hide_index=True, height=360)


def ensure_manual_state(task_name, stochastic, seed):
    config = {"task_name": task_name, "stochastic": stochastic, "seed": seed}
    if st.session_state.get("manual_config") != config:
        env = StudyPlannerEnv(task_name=task_name, stochastic=stochastic, seed=seed)
        observation = env.reset()
        st.session_state.manual_env = env
        st.session_state.manual_obs = observation
        st.session_state.manual_done = False
        st.session_state.manual_history = []
        st.session_state.manual_config = config


def render_manual_lab(task_name, stochastic, seed):
    ensure_manual_state(task_name, stochastic, seed)
    env = st.session_state.manual_env
    observation = st.session_state.manual_obs
    done = st.session_state.manual_done

    st.markdown("### Manual Simulation Lab")
    control_cols = st.columns([1.2, 1, 1])
    with control_cols[0]:
        chosen_action = st.selectbox("Choose next action", options=list(ACTION_LABELS.keys()), format_func=lambda x: ACTION_LABELS[x])
    with control_cols[1]:
        step_clicked = st.button("Apply Action", use_container_width=True, disabled=done)
    with control_cols[2]:
        reset_clicked = st.button("Reset Manual Lab", use_container_width=True)

    if reset_clicked:
        st.session_state.manual_config = None
        ensure_manual_state(task_name, stochastic, seed)
        env = st.session_state.manual_env
        observation = st.session_state.manual_obs
        done = st.session_state.manual_done

    if step_clicked and not done:
        next_obs, reward, done, info = env.step(chosen_action)
        st.session_state.manual_obs = next_obs
        st.session_state.manual_done = done
        st.session_state.manual_history.append(
            {
                "step": len(st.session_state.manual_history) + 1,
                "action": ACTION_LABELS[chosen_action],
                "reward": reward,
                "day": next_obs["day"],
                "energy": next_obs["energy"],
                "avg_mastery": next_obs["avg_mastery"],
                "imbalance": next_obs["imbalance"],
                "cognitive_load": next_obs.get("cognitive_load", 0.0),
                "recovery_score": next_obs.get("recovery_score", 0.0),
                "reward_breakdown": info.get("reward_breakdown", {}),
            }
        )
        observation = next_obs

    top_cols = st.columns(4)
    top_cols[0].metric("Day", observation["day"])
    top_cols[1].metric("Energy", observation["energy"])
    top_cols[2].metric("Average Mastery", observation["avg_mastery"])
    top_cols[3].metric("Imbalance", observation["imbalance"])

    state_cols = st.columns(2)
    state_cols[0].metric("Cognitive Load", observation.get("cognitive_load", 0.0))
    state_cols[1].metric("Recovery Score", observation.get("recovery_score", 0.0))

    mastery_cols = st.columns(3)
    for col, subject in zip(mastery_cols, ("math", "physics", "chemistry")):
        col.metric(
            subject.title(),
            observation["mastery"][subject],
            delta=f"memory {observation.get('memory_strength', {}).get(subject, 0.0):.4f}",
        )

    if st.session_state.manual_history:
        last = st.session_state.manual_history[-1]
        st.markdown("**Latest reward breakdown**")
        component_rows = [{"component": key, "value": value} for key, value in last["reward_breakdown"].items()]
        st.bar_chart(component_rows, x="component", y="value")
        st.markdown("**Current retention risk**")
        risk_rows = [{"subject": key, "risk": value} for key, value in observation.get("retention_risk", {}).items()]
        st.bar_chart(risk_rows, x="subject", y="risk")
        st.dataframe(st.session_state.manual_history, use_container_width=True, hide_index=True, height=240)
    else:
        st.info("Step through the environment manually to inspect reward components, retention risk, and state transitions.")


def render_compare(task_name):
    st.markdown("### Agent Comparison")
    compare_col1, compare_col2 = st.columns(2)
    heuristic_summary = run_episode_cached(task_name, stochastic=False, seed=123, agent_mode="heuristic")

    with compare_col1:
        st.markdown("**Heuristic baseline**")
        st.metric("Total Reward", heuristic_summary["total_reward"])
        st.metric("Average Mastery", heuristic_summary["episode_summary"]["average_mastery"])
        st.metric("Memory Strength", heuristic_summary["episode_summary"].get("average_memory_strength", 0.0))
        st.metric("Balance Gap", heuristic_summary["episode_summary"]["balance_gap"])

    with compare_col2:
        st.markdown("**OpenAI-ready baseline**")
        if safe_has_openai_key():
            st.info("OpenAI baseline can be executed when OPENAI_API_KEY is configured in the environment.")
        else:
            st.info("Set OPENAI_API_KEY to run the OpenAI baseline. The app keeps the deterministic baseline available for offline usage.")

    comparison_rows = [
        {
            "agent": "heuristic",
            "total_reward": heuristic_summary["total_reward"],
            "average_mastery": heuristic_summary["episode_summary"]["average_mastery"],
            "memory_strength": heuristic_summary["episode_summary"].get("average_memory_strength", 0.0),
            "balance_gap": heuristic_summary["episode_summary"]["balance_gap"],
            "energy_left": heuristic_summary["episode_summary"]["energy_left"],
            "steps": heuristic_summary["steps"],
        }
    ]
    st.dataframe(comparison_rows, use_container_width=True, hide_index=True)


def main():
    st.set_page_config(page_title=APP_NAME, page_icon="📚", layout="wide")

    if "appearance" not in st.session_state:
        st.session_state.appearance = "Dark"

    with st.sidebar:
        appearance = st.segmented_control(
            "Appearance",
            options=["Dark", "Light"],
            default=st.session_state.appearance,
            selection_mode="single",
        )
        st.session_state.appearance = appearance
        inject_styles(appearance.lower())
        render_logo(132, framed=True)
        st.markdown(f"### {APP_NAME}")
        st.caption("Liquid-glass study planning simulator")
        st.markdown("---")
        st.markdown("## Simulation Controls")
        st.caption("Configure the planner, then run a full episode.")
        task_name = st.selectbox("Task difficulty", options=list(TASKS.keys()), index=1)
        mode = st.radio("Execution mode", options=["deterministic", "stochastic", "randomize"], index=0)
        seed = st.number_input("Seed", min_value=0, value=123, step=1, disabled=(mode == "randomize"))
        st.markdown("---")
        task = TASKS[task_name]
        st.markdown(
            f"""
            <div class="glass-note">
                <strong>Task profile</strong><br><br>
                Days: <code>{task['days']}</code><br>
                Daily target: <code>{task['daily_target']}</code><br>
                Max energy: <code>{task['max_energy']}</code><br>
                Decay rate: <code>{task['decay_rate']}</code><br>
                Spacing target: <code>{task['spacing_target']}</code>
            </div>
            """,
            unsafe_allow_html=True,
        )
        run_clicked = st.button("Run Simulation", type="primary", use_container_width=True)

    render_hero()

    if "summary" not in st.session_state:
        st.session_state.summary = None
    if "manual_config" not in st.session_state:
        st.session_state.manual_config = None
    if "run_history" not in st.session_state:
        st.session_state.run_history = []

    stochastic = mode in {"stochastic", "randomize"}
    actual_seed = None if mode == "randomize" else int(seed)

    if run_clicked:
        summary = run_episode_cached(task_name, stochastic=stochastic, seed=actual_seed, agent_mode="heuristic")
        review = build_run_review(summary)
        mode_label = "randomized" if actual_seed is None else ("stochastic" if stochastic else "deterministic")
        st.session_state.summary = summary
        st.session_state.run_history.insert(
            0,
            {
                "time": datetime.now().strftime("%H:%M:%S"),
                "task": task_name,
                "mode": mode_label,
                "seed": "auto" if actual_seed is None else actual_seed,
                "reward": round(summary["total_reward"], 4),
                "review": review["verdict"],
                "badge_class": review["badge_class"],
                "feedback": review["feedback"],
            },
        )
        st.session_state.run_history = st.session_state.run_history[:20]

    summary = st.session_state.summary
    if summary is None:
        st.info(f"Pick a task profile and run the planner to open the liquid-glass {APP_VERSION} analytics workspace.")
        return

    render_metric_panels(summary)
    st.markdown("")
    render_subject_cards(summary)
    st.markdown("")
    render_plan_snapshot(summary)
    st.markdown("")
    render_run_review(summary)

    overview_tab, manual_tab, compare_tab = st.tabs(["Overview", "Manual Lab", "Compare"])
    with overview_tab:
        render_analytics(summary)
    with manual_tab:
        render_manual_lab(task_name, stochastic, actual_seed)
    with compare_tab:
        render_compare(task_name)


if __name__ == "__main__":
    main()
