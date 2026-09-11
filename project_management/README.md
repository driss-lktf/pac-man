# Project Management

This directory gathers the evidence of how the **Pac-Man** project was driven.

## Approach

We used a lightweight **Kanban** board combined with an **acceptance-test**
checklist derived directly from the subject. Work was sliced into small,
independently testable features (config, maze, entities, rules, UI,
packaging) so the game stayed runnable at every step.

## Contents

| File | Purpose |
|------|---------|
| [`kanban.md`](kanban.md) | Timeline, Kanban board and progress tracking |
| [`risks.md`](risks.md) | Risk analysis and mitigations |
| [`test_plan.md`](test_plan.md) | Acceptance test plan (features, results) |
| [`team.md`](team.md) | Team organization and decision log |
| [`packaging.md`](packaging.md) | How to package & deploy to Itch.io |

## Tools

- **Git** for version control (feature-oriented commits).
- This Markdown board for planning and tracking.
- `make lint` / `make test` as continuous quality gates.
