from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from inference import run_episode

ASSETS_DIR = ROOT / "ui" / "assets"
SCREENSHOT_PATH = ASSETS_DIR / "dashboard-preview.svg"
ANIMATED_PATH = ASSETS_DIR / "planner-walkthrough.svg"


def build_screenshot_svg():
    summary = run_episode("medium", stochastic=False, seed=123)
    episode = summary["episode_summary"]
    trace = summary["trace"]
    mastery = summary["final_state"]["mastery"]

    energy_points = []
    mastery_points = []
    for idx, row in enumerate(trace):
        x = 95 + idx * (505 / max(len(trace) - 1, 1))
        energy_y = 775 - 185 * (row["energy"] / 10.0)
        avg_y = 775 - 185 * row["avg_mastery"]
        energy_points.append(f"{x:.1f},{energy_y:.1f}")
        mastery_points.append(f"{x + 690:.1f},{avg_y:.1f}")

    svg = f"""<svg width="1600" height="1000" viewBox="0 0 1600 1000" fill="none" xmlns="http://www.w3.org/2000/svg">
<rect width="1600" height="1000" rx="36" fill="#EEF4FF"/>
<rect x="36" y="36" width="1528" height="928" rx="36" fill="#F4F8FF" stroke="#D9E4F5" stroke-width="2"/>
<rect x="66" y="62" width="1468" height="156" rx="30" fill="white" stroke="#D8E3F4" stroke-width="2"/>
<text x="96" y="98" fill="#0F766E" font-family="Segoe UI, Arial, sans-serif" font-size="18" font-weight="700">EDUDYNAMICS</text>
<text x="96" y="145" fill="#0F172A" font-family="Segoe UI, Arial, sans-serif" font-size="34" font-weight="800">Energy-aware study optimization dashboard</text>
<text x="96" y="187" fill="#475569" font-family="Segoe UI, Arial, sans-serif" font-size="20">Deterministic baseline on the medium task balancing math, physics, chemistry, reward quality, and fatigue.</text>

<rect x="68" y="246" width="332" height="150" rx="28" fill="white" stroke="#D8E3F4" stroke-width="2"/>
<rect x="436" y="246" width="332" height="150" rx="28" fill="white" stroke="#D8E3F4" stroke-width="2"/>
<rect x="804" y="246" width="332" height="150" rx="28" fill="white" stroke="#D8E3F4" stroke-width="2"/>
<rect x="1172" y="246" width="332" height="150" rx="28" fill="white" stroke="#D8E3F4" stroke-width="2"/>

<text x="92" y="276" fill="#64748B" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700">TOTAL REWARD</text>
<text x="92" y="332" fill="#0F172A" font-family="Segoe UI, Arial, sans-serif" font-size="34" font-weight="800">{summary["total_reward"]}</text>
<text x="92" y="370" fill="#64748B" font-family="Segoe UI, Arial, sans-serif" font-size="18">Composite policy quality</text>

<text x="460" y="276" fill="#64748B" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700">AVG MASTERY</text>
<text x="460" y="332" fill="#0F172A" font-family="Segoe UI, Arial, sans-serif" font-size="34" font-weight="800">{episode["average_mastery"]}</text>
<text x="460" y="370" fill="#64748B" font-family="Segoe UI, Arial, sans-serif" font-size="18">End-of-episode performance</text>

<text x="828" y="276" fill="#64748B" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700">BALANCE GAP</text>
<text x="828" y="332" fill="#0F172A" font-family="Segoe UI, Arial, sans-serif" font-size="34" font-weight="800">{episode["balance_gap"]}</text>
<text x="828" y="370" fill="#64748B" font-family="Segoe UI, Arial, sans-serif" font-size="18">Lower means more even coverage</text>

<text x="1196" y="276" fill="#64748B" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700">ENERGY LEFT</text>
<text x="1196" y="332" fill="#0F172A" font-family="Segoe UI, Arial, sans-serif" font-size="34" font-weight="800">{episode["energy_left"]}</text>
<text x="1196" y="370" fill="#64748B" font-family="Segoe UI, Arial, sans-serif" font-size="18">Recovery preserved at finish</text>

<rect x="68" y="426" width="452" height="158" rx="26" fill="#0F766E"/>
<rect x="562" y="426" width="452" height="158" rx="26" fill="#1D4ED8"/>
<rect x="1056" y="426" width="452" height="158" rx="26" fill="#C2410C"/>

<text x="92" y="458" fill="white" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700">MATH</text>
<text x="92" y="512" fill="white" font-family="Segoe UI, Arial, sans-serif" font-size="30" font-weight="800">{mastery["math"]:.4f}</text>
<rect x="92" y="536" width="404" height="14" rx="7" fill="#FFFFFF33"/><rect x="92" y="536" width="{404 * mastery["math"]:.1f}" height="14" rx="7" fill="white"/>

<text x="586" y="458" fill="white" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700">PHYSICS</text>
<text x="586" y="512" fill="white" font-family="Segoe UI, Arial, sans-serif" font-size="30" font-weight="800">{mastery["physics"]:.4f}</text>
<rect x="586" y="536" width="404" height="14" rx="7" fill="#FFFFFF33"/><rect x="586" y="536" width="{404 * mastery["physics"]:.1f}" height="14" rx="7" fill="white"/>

<text x="1080" y="458" fill="white" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700">CHEMISTRY</text>
<text x="1080" y="512" fill="white" font-family="Segoe UI, Arial, sans-serif" font-size="30" font-weight="800">{mastery["chemistry"]:.4f}</text>
<rect x="1080" y="536" width="404" height="14" rx="7" fill="#FFFFFF33"/><rect x="1080" y="536" width="{404 * mastery["chemistry"]:.1f}" height="14" rx="7" fill="white"/>

<rect x="68" y="620" width="712" height="316" rx="24" fill="white" stroke="#D8E3F4" stroke-width="2"/>
<rect x="818" y="620" width="712" height="316" rx="24" fill="white" stroke="#D8E3F4" stroke-width="2"/>
<text x="96" y="656" fill="#0F172A" font-family="Segoe UI, Arial, sans-serif" font-size="18" font-weight="700">Energy trajectory</text>
<text x="846" y="656" fill="#0F172A" font-family="Segoe UI, Arial, sans-serif" font-size="18" font-weight="700">Average mastery trajectory</text>
<rect x="92" y="676" width="664" height="224" rx="18" fill="#F8FBFF" stroke="#E2EAF7"/>
<rect x="842" y="676" width="664" height="224" rx="18" fill="#F8FBFF" stroke="#E2EAF7"/>
<polyline fill="none" stroke="#0F766E" stroke-width="5" points="{' '.join(energy_points)}"/>
<polyline fill="none" stroke="#1D4ED8" stroke-width="5" points="{' '.join(mastery_points)}"/>
</svg>
"""
    SCREENSHOT_PATH.write_text(svg, encoding="utf-8")


def build_animated_walkthrough_svg():
    summary = run_episode("medium", stochastic=True, seed=42)
    trace = summary["trace"]
    selected = [trace[i] for i in [0, 2, 5, 8, 11, 14, 18, 22, 26, len(trace) - 1]]

    animations = []
    step_text = []
    reward_text = []
    action_text = []
    energy_path = []
    mastery_path = []

    for idx, item in enumerate(selected):
        begin = f"{idx * 0.9}s"
        display = "inline" if idx == 0 else "none"
        step_text.append(
            f'<text id="step{idx}" x="96" y="224" fill="#0F172A" font-family="Segoe UI, Arial, sans-serif" font-size="34" font-weight="800" display="{display}">{item["step"]}<set attributeName="display" to="inline" begin="{begin}" dur="0.88s" /></text>'
        )
        cum_reward = round(sum(frame["reward"] for frame in trace[: item["step"]]), 4)
        reward_text.append(
            f'<text id="reward{idx}" x="402" y="224" fill="#0F172A" font-family="Segoe UI, Arial, sans-serif" font-size="34" font-weight="800" display="{display}">{cum_reward}<set attributeName="display" to="inline" begin="{begin}" dur="0.88s" /></text>'
        )
        action = f'{item["action"]["type"]}:{item["action"]["subject"] or "all"}'
        action_text.append(
            f'<text id="action{idx}" x="742" y="224" fill="#0F172A" font-family="Segoe UI, Arial, sans-serif" font-size="30" font-weight="800" display="{display}">{action}<set attributeName="display" to="inline" begin="{begin}" dur="0.88s" /></text>'
        )

        upto = trace[: item["step"]]
        energy_points = []
        mastery_points = []
        for p_idx, row in enumerate(upto):
            px = 104 + p_idx * (972 / max(len(upto) - 1, 1))
            energy_y = 614 - 176 * (row["energy"] / 10.0)
            mastery_y = 614 - 176 * row["avg_mastery"]
            energy_points.append(f"{px:.1f},{energy_y:.1f}")
            mastery_points.append(f"{px:.1f},{mastery_y:.1f}")

        energy_path.append(
            f'<polyline points="{" ".join(energy_points)}" fill="none" stroke="#0F766E" stroke-width="5" display="{display}"><set attributeName="display" to="inline" begin="{begin}" dur="0.88s" /></polyline>'
        )
        mastery_path.append(
            f'<polyline points="{" ".join(mastery_points)}" fill="none" stroke="#1D4ED8" stroke-width="5" display="{display}"><set attributeName="display" to="inline" begin="{begin}" dur="0.88s" /></polyline>'
        )

    total_duration = len(selected) * 0.9
    svg = f"""<svg width="1200" height="720" viewBox="0 0 1200 720" fill="none" xmlns="http://www.w3.org/2000/svg">
<rect width="1200" height="720" rx="32" fill="#F7FBFF"/>
<rect x="32" y="28" width="1136" height="660" rx="32" fill="white" stroke="#D8E3F4" stroke-width="2"/>
<text x="64" y="72" fill="#0F172A" font-family="Segoe UI, Arial, sans-serif" font-size="34" font-weight="800">Study Planner Walkthrough</text>
<text x="64" y="110" fill="#475569" font-family="Segoe UI, Arial, sans-serif" font-size="18">Animated summary of one medium-task rollout</text>

<rect x="64" y="142" width="302" height="132" rx="28" fill="white" stroke="#D8E3F4" stroke-width="2"/>
<rect x="390" y="142" width="302" height="132" rx="28" fill="white" stroke="#D8E3F4" stroke-width="2"/>
<rect x="716" y="142" width="420" height="132" rx="28" fill="white" stroke="#D8E3F4" stroke-width="2"/>

<text x="88" y="176" fill="#64748B" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700">CURRENT STEP</text>
<text x="414" y="176" fill="#64748B" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700">CUMULATIVE REWARD</text>
<text x="740" y="176" fill="#64748B" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700">CURRENT ACTION</text>
{''.join(step_text)}
{''.join(reward_text)}
{''.join(action_text)}

<rect x="64" y="316" width="1072" height="334" rx="28" fill="white" stroke="#D8E3F4" stroke-width="2"/>
<text x="88" y="352" fill="#0F172A" font-family="Segoe UI, Arial, sans-serif" font-size="18" font-weight="700">Energy and mastery over time</text>
<rect x="92" y="380" width="1016" height="240" rx="18" fill="#F8FBFF" stroke="#E2EAF7"/>
<text x="950" y="410" fill="#0F766E" font-family="Segoe UI, Arial, sans-serif" font-size="15" font-weight="700">energy</text>
<text x="950" y="434" fill="#1D4ED8" font-family="Segoe UI, Arial, sans-serif" font-size="15" font-weight="700">avg mastery</text>
{''.join(energy_path)}
{''.join(mastery_path)}

<text x="64" y="682" fill="#64748B" font-family="Segoe UI, Arial, sans-serif" font-size="14">Loop duration: {total_duration:.1f}s | Stochastic seed: 42</text>
</svg>
"""
    ANIMATED_PATH.write_text(svg, encoding="utf-8")


def main():
    ASSETS_DIR.mkdir(exist_ok=True)
    build_screenshot_svg()
    build_animated_walkthrough_svg()
    print(f"Created {SCREENSHOT_PATH}")
    print(f"Created {ANIMATED_PATH}")


if __name__ == "__main__":
    main()
