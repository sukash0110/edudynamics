---
title: Student Study Planner
emoji: 📚
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8501
pinned: false
license: mit
short_description: Streamlit app for a study planning environment with energy and balance optimization.
---

# Student Study Planner with Energy, Balance, and Performance Optimization

This project implements an OpenEnv-style study planning environment for a student managing math, physics, and chemistry across multiple days.

## Features

- Full environment API with `reset()`, `step(action)`, and `state()`
- Multi-day simulation with three time slots per day
- Actions for focused study, revision, and rest
- Energy-aware transitions and subject mastery tracking
- Reward shaped by:
  - average performance improvement
  - cross-subject balance
  - energy efficiency
  - penalties for imbalance and poor energy usage
- Three tasks: `easy`, `medium`, and `hard`
- Deterministic baseline policy that adapts to energy and mastery imbalance
- Optional stochastic mode for varied runs

## Project Structure

```text
study_planner_env/
├── study_env/
│   ├── __init__.py
│   ├── env.py
│   ├── tasks.py
├── app.py
├── inference.py
├── grader.py
├── openenv.yaml
├── README.md
├── Dockerfile
└── requirements.txt
```

## Actions

The environment supports the following actions:

- `0`: study math
- `1`: study physics
- `2`: study chemistry
- `3`: revise math
- `4`: revise physics
- `5`: revise chemistry
- `6`: rest

## Running

```bash
python inference.py
```

Varied run:

```bash
python inference.py --stochastic --seed 42
```

Fully random run:

```bash
python inference.py --randomize
```

Optional grading run:

```bash
python grader.py
```

Streamlit UI:

```bash
streamlit run app.py
```

## Deploy to Hugging Face Spaces

This repo is configured for a Docker-based Space, which is the recommended route for Streamlit apps because the built-in Streamlit SDK is deprecated in the current Hugging Face docs.

1. Create a new Space on Hugging Face.
2. Choose `Docker` as the Space SDK.
3. Upload or push the contents of this folder.
4. Hugging Face will build the included `Dockerfile` and launch the app on port `8501`.

If you want to push with git:

```bash
git init
git remote add origin https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
git add .
git commit -m "Initial Hugging Face Space"
git push origin main
```

## Environment Notes

- Each episode spans a configured number of days.
- Each day has three decision slots.
- Studying gives larger gains but costs more energy.
- Revision reinforces one subject and slightly supports others.
- Rest restores energy but can be mildly penalized if used wastefully.
- The baseline agent is deterministic, so results are reproducible across runs.
- Use `--stochastic` to introduce controlled randomness while keeping runs reproducible for a given seed.
- Use `--randomize` to get a different stochastic seed automatically on each run.
- The Streamlit app provides a visual way to run simulations and inspect results.
