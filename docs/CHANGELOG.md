# Changelog

Release notes for `EduDynamics` starting from version `1.0.0`.

## 1.1.0

Focus: major bug fixes and quality improvements.

- added persistent appearance selection in the Streamlit UI instead of relying on browser theme detection
- improved light-mode polish for header chrome, controls, cards, and info panels
- added cached episode execution for smoother compare views and fewer unnecessary reruns
- centralized app/version branding in the UI to reduce copy drift
- aligned the landing page, API metadata, package metadata, and README to the same release version
- kept hybrid deployment and validator compliance intact

## 1.0.3

Focus: realistic learning integration plus the polished liquid-glass UI line.

- introduced more realistic learning dynamics with:
  - memory strength
  - retention risk
  - spacing-aware gains
  - forgetting and consolidation
  - cognitive load and recovery
- upgraded the heuristic baseline to respond to retention risk and load, not only mastery imbalance
- expanded analytics with:
  - reward component charts
  - memory strength trends
  - retention risk trends
  - richer trace data
- refined the hybrid Hugging Face deployment so the UI and API can coexist
- clarified branding split between `EduDynamics` and the `AuraUI` interface layer

## 1.0.2

Focus: UI milestone in the `1.0.x` line.

- introduced the Apple-inspired liquid-glass visual direction for the Streamlit interface
- redesigned the dashboard around glass panels, stronger gradients, and more premium controls
- improved hero, sidebar, subject cards, and dashboard hierarchy

Note:
- this was a design milestone during the `1.0.x` cycle and the resulting work is reflected in the later `1.0.3` release line

## 1.0.1

Focus: analytics and interaction improvements.

- added a richer analytics workspace in the Streamlit UI
- introduced the manual simulation lab for step-by-step environment control
- added reward breakdown views and stronger episode trace inspection
- added comparison views for the heuristic baseline
- aligned package metadata, README metadata, and deployment copy around the first post-`1.0.0` release

## 1.0.0

Focus: first stable OpenEnv-compatible release.

- implemented the `StudyPlannerEnv` environment with:
  - `reset()`
  - `step(action)`
  - `state()`
- modeled:
  - multiple subjects
  - energy constraints
  - study, revise, and rest actions
  - multi-day progression
- added three tasks: `easy`, `medium`, and `hard`
- created a deterministic baseline policy agent
- added a grader with normalized task scores
- added Docker packaging and Hugging Face deployment support
- added OpenEnv validation support and submission checks

