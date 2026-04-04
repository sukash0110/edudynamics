import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

import yaml

from evaluation.grader_runner import grade


ROOT = Path(__file__).resolve().parents[1]


def http_json(method, url, data=None):
    payload = None if data is None else json.dumps(data).encode("utf-8")
    request = Request(url, data=payload, method=method)
    request.add_header("Content-Type", "application/json")
    with urlopen(request, timeout=10) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def validate_openenv_yaml():
    config = yaml.safe_load((ROOT / "openenv.yaml").read_text(encoding="utf-8"))
    required_top_level = {"name", "entrypoint", "api", "environment", "tasks", "agent", "grader"}
    missing = required_top_level.difference(config)
    if missing:
        raise AssertionError(f"openenv.yaml missing keys: {sorted(missing)}")
    assert config["entrypoint"] == "inference.py"
    assert len(config["tasks"]) >= 3
    required_env = {"API_BASE_URL", "MODEL_NAME", "HF_TOKEN"}
    declared = set(config.get("environment_variables", []))
    assert required_env.issubset(declared)


def validate_inference():
    start = time.time()
    completed = subprocess.run(
        [sys.executable, "inference.py", "--agent", "heuristic"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=1200,
        check=True,
    )
    duration = time.time() - start
    assert duration < 1200
    assert "[START] task=easy" in completed.stdout
    assert "[START] task=medium" in completed.stdout
    assert "[START] task=hard" in completed.stdout
    assert "[END] success=" in completed.stdout


def validate_grader():
    result = grade()
    assert 0.0 <= result["overall_score"] <= 1.0
    assert result["total_tasks"] >= 3
    for task_name, task_result in result["task_results"].items():
        assert task_name
        assert 0.0 <= task_result["score"] <= 1.0


def validate_server():
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "study_env.api:app", "--host", "127.0.0.1", "--port", "8510"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                status, payload = http_json("GET", "http://127.0.0.1:8510/health")
                if status == 200 and payload["status"] == "ok":
                    break
            except URLError:
                time.sleep(0.5)
        else:
            raise AssertionError("server did not become ready")

        status, reset_payload = http_json("POST", "http://127.0.0.1:8510/reset", {"task_name": "easy", "stochastic": False, "seed": 123})
        assert status == 200
        assert reset_payload["observation"]["task"] == "easy"

        status, state_payload = http_json("GET", "http://127.0.0.1:8510/state")
        assert status == 200
        assert "energy" in state_payload

        status, step_payload = http_json("POST", "http://127.0.0.1:8510/step", {"action": 0})
        assert status == 200
        assert isinstance(step_payload["reward"], float)
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def validate_dockerfile():
    content = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "server.app" in content or "study_env.api:app" in content
    assert "EXPOSE 8501" in content


def main():
    validate_openenv_yaml()
    validate_dockerfile()
    validate_inference()
    validate_grader()
    validate_server()
    print("Validation passed")


if __name__ == "__main__":
    main()
