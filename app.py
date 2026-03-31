import streamlit as st

from inference import run_episode
from study_env.tasks import TASKS


def build_trace_frame(trace_tail):
    rows = []
    for item in trace_tail:
        action = item["action"]
        rows.append(
            {
                "step": item["step"],
                "day": item["day"],
                "energy": item["energy"],
                "avg_mastery": item["avg_mastery"],
                "imbalance": item["imbalance"],
                "action_type": action["type"],
                "subject": action["subject"] or "all",
                "reward": item["reward"],
            }
        )
    return rows


def render_metrics(summary):
    episode = summary["episode_summary"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Reward", summary["total_reward"])
    col2.metric("Average Mastery", episode.get("average_mastery"))
    col3.metric("Balance Gap", episode.get("balance_gap"))
    col4.metric("Energy Left", episode.get("energy_left"))


def render_final_state(summary):
    final_state = summary["final_state"]
    mastery = final_state["mastery"]

    st.subheader("Final State")
    st.write(
        {
            "task": final_state["task"],
            "day": final_state["day"],
            "remaining_days": final_state["remaining_days"],
            "energy": final_state["energy"],
            "avg_mastery": final_state["avg_mastery"],
            "imbalance": final_state["imbalance"],
            "mode": "stochastic" if summary["stochastic"] else "deterministic",
            "seed": summary["seed"],
        }
    )

    st.subheader("Subject Mastery")
    st.bar_chart(mastery)


def main():
    st.set_page_config(page_title="Study Planner Env", layout="wide")
    st.title("Student Study Planner")
    st.caption("Energy, balance, and performance optimization over multiple study days.")

    with st.sidebar:
        st.header("Controls")
        task_name = st.selectbox("Task", options=list(TASKS.keys()), index=0)
        mode = st.radio("Mode", options=["deterministic", "stochastic", "randomize"], index=0)
        seed = st.number_input("Seed", min_value=0, value=123, step=1, disabled=(mode == "randomize"))
        run_clicked = st.button("Run Simulation", type="primary", use_container_width=True)

    if "summary" not in st.session_state:
        st.session_state.summary = None

    if run_clicked:
        stochastic = mode in {"stochastic", "randomize"}
        actual_seed = None if mode == "randomize" else int(seed)
        summary = run_episode(task_name, stochastic=stochastic, seed=actual_seed)
        st.session_state.summary = summary

    summary = st.session_state.summary
    if summary is None:
        st.info("Choose a task and mode, then click Run Simulation.")
        return

    st.subheader("Run Summary")
    render_metrics(summary)

    info_col, state_col = st.columns([1, 1])
    with info_col:
        st.write(
            {
                "task": summary["task"],
                "mode": "stochastic" if summary["stochastic"] else "deterministic",
                "seed": summary["seed"],
                "steps": summary["steps"],
            }
        )
    with state_col:
        render_final_state(summary)

    st.subheader("Recent Trace")
    trace_frame = build_trace_frame(summary["trace_tail"])
    st.dataframe(trace_frame, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
