import streamlit as st

from inference import run_episode
from study_env.tasks import TASKS


LOGO_PATH = "assets/edudynamics-logo.svg"

SUBJECT_COLORS = {
    "math": "#0f766e",
    "physics": "#1d4ed8",
    "chemistry": "#c2410c",
}


def inject_styles():
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(13, 148, 136, 0.18), transparent 28%),
                radial-gradient(circle at top right, rgba(29, 78, 216, 0.18), transparent 30%),
                linear-gradient(180deg, #f4f7f4 0%, #eef4ff 100%);
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .hero {
            border: 1px solid rgba(15, 23, 42, 0.08);
            background: linear-gradient(135deg, rgba(255,255,255,0.96), rgba(239,246,255,0.92));
            border-radius: 24px;
            padding: 1.5rem 1.6rem;
            box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
            margin-bottom: 1rem;
        }
        .hero-kicker {
            color: #0f766e;
            font-size: 0.84rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.4rem;
        }
        .hero-title {
            color: #0f172a;
            font-size: 2.2rem;
            line-height: 1.05;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }
        .hero-copy {
            color: #334155;
            font-size: 1rem;
            line-height: 1.55;
            max-width: 48rem;
        }
        .panel {
            border: 1px solid rgba(15, 23, 42, 0.08);
            background: rgba(255, 255, 255, 0.82);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 1.1rem 1.2rem;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
        }
        .mini-label {
            color: #64748b;
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        .big-number {
            color: #0f172a;
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.1;
            margin-top: 0.35rem;
        }
        .support-text {
            color: #475569;
            font-size: 0.92rem;
            margin-top: 0.25rem;
        }
        .subject-card {
            border-radius: 18px;
            padding: 1rem;
            color: white;
            min-height: 112px;
            box-shadow: 0 12px 24px rgba(15, 23, 42, 0.12);
        }
        .subject-name {
            font-size: 0.82rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 700;
            opacity: 0.9;
        }
        .subject-value {
            font-size: 2rem;
            font-weight: 800;
            margin-top: 0.25rem;
        }
        .subject-caption {
            font-size: 0.92rem;
            opacity: 0.9;
            margin-top: 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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
                "reward": item["reward"],
                "action_type": action["type"],
                "subject": action["subject"] or "all",
            }
        )
    return rows


def render_hero():
    logo_col, copy_col = st.columns([0.95, 3.05], vertical_alignment="center")
    with logo_col:
        st.image(LOGO_PATH, use_container_width=True)
    with copy_col:
        st.markdown(
            """
            <div class="hero">
                <div class="hero-kicker">EduDynamics</div>
                <div class="hero-title">Build sustainable study momentum across math, physics, and chemistry.</div>
                <div class="hero-copy">
                    This dashboard simulates a student balancing performance, energy, and subject coverage over multiple days.
                    Run deterministic baselines for reproducible evaluation, or switch to stochastic modes to explore varied trajectories.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_metric_panels(summary):
    episode = summary["episode_summary"]
    cards = [
        ("Total Reward", summary["total_reward"], "Composite score across performance, balance, and energy use."),
        ("Average Mastery", episode.get("average_mastery"), "Final mastery averaged across all three subjects."),
        ("Balance Gap", episode.get("balance_gap"), "Lower is better. Zero means perfectly balanced learning."),
        ("Energy Left", episode.get("energy_left"), "Remaining energy at the end of the episode."),
    ]
    columns = st.columns(4)
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
    avg_mastery = summary["episode_summary"]["average_mastery"]
    cols = st.columns(3)
    for col, subject in zip(cols, ("math", "physics", "chemistry")):
        value = mastery[subject]
        color = SUBJECT_COLORS[subject]
        delta = round(value - avg_mastery, 4)
        caption = "Above plan average" if delta >= 0 else "Below plan average"
        col.markdown(
            f"""
            <div class="subject-card" style="background: linear-gradient(160deg, {color}, rgba(15, 23, 42, 0.92));">
                <div class="subject-name">{subject}</div>
                <div class="subject-value">{value:.4f}</div>
                <div class="subject-caption">{caption}: {delta:+.4f}</div>
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
                    Mode: <strong>{mode_label}</strong><br>
                    Seed: <strong>{seed_label}</strong><br>
                    Steps executed: <strong>{summary["steps"]}</strong>
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
    with right:
        st.markdown("### Reward Design")
        st.markdown(
            """
            <div class="panel">
                <div class="support-text">
                    The episode reward blends four signals:
                    <br><br>
                    <strong>Performance</strong> rewards mastery gains.
                    <br>
                    <strong>Balance</strong> favors even subject coverage.
                    <br>
                    <strong>Energy efficiency</strong> rewards progress per unit of effort.
                    <br>
                    <strong>Penalties</strong> discourage imbalance and poor recovery choices.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_trace(summary):
    rows = build_trace_rows(summary["trace"])
    st.markdown("### Episode Trace")

    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.markdown("**Energy trajectory**")
        st.line_chart([{"step": row["step"], "energy": row["energy"]} for row in rows], x="step", y="energy")
    with chart_cols[1]:
        st.markdown("**Mastery trajectory**")
        st.line_chart(
            [{"step": row["step"], "avg_mastery": row["avg_mastery"]} for row in rows],
            x="step",
            y="avg_mastery",
        )

    view = st.segmented_control(
        "Trace view",
        options=["Recent", "Full"],
        default="Recent",
        selection_mode="single",
    )
    if view == "Recent":
        st.dataframe(rows[-8:], use_container_width=True, hide_index=True)
    else:
        st.dataframe(rows, use_container_width=True, hide_index=True, height=360)

    focus_step = st.slider("Inspect step", min_value=1, max_value=len(rows), value=len(rows))
    detail = rows[focus_step - 1]
    st.markdown(
        f"""
        <div class="panel">
            <div class="mini-label">Step {detail["step"]}</div>
            <div class="support-text">
                Day <strong>{detail["day"]}</strong> |
                Action <strong>{detail["action_type"]}:{detail["subject"]}</strong> |
                Reward <strong>{detail["reward"]}</strong><br>
                Energy <strong>{detail["energy"]}</strong> |
                Avg mastery <strong>{detail["avg_mastery"]}</strong> |
                Imbalance <strong>{detail["imbalance"]}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(page_title="EduDynamics", page_icon="📚", layout="wide")
    inject_styles()
    render_hero()

    with st.sidebar:
        st.image(LOGO_PATH, width=132)
        st.markdown("### EduDynamics")
        st.caption("Energy-aware student planning simulator")
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
            **Task profile**

            - Days: `{task['days']}`
            - Daily target: `{task['daily_target']}`
            - Max energy: `{task['max_energy']}`
            """
        )
        run_clicked = st.button("Run Simulation", type="primary", use_container_width=True)

    if "summary" not in st.session_state:
        st.session_state.summary = None

    if run_clicked:
        stochastic = mode in {"stochastic", "randomize"}
        actual_seed = None if mode == "randomize" else int(seed)
        st.session_state.summary = run_episode(task_name, stochastic=stochastic, seed=actual_seed)

    summary = st.session_state.summary
    if summary is None:
        st.info("Pick a task profile and run the planner to see the simulation dashboard.")
        return

    render_metric_panels(summary)
    st.markdown("")
    render_subject_cards(summary)
    st.markdown("")
    render_plan_snapshot(summary)
    st.markdown("")
    render_trace(summary)


if __name__ == "__main__":
    main()
