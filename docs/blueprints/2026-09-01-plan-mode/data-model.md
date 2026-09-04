# Data model

## Domain types

```text
PlanDraft
  id: UUID
  goal: string
  approaches: PlanApproach[1..3]
  selected_approach_id: string | null
  organizer_project_id: string | null
  status: draft | ready | running | succeeded | failed | cancelled | blocked

PlanApproach
  id: string
  title: string
  summary: string
  recommended: boolean
  steps: PlanStep[1..N]

PlanStep
  id: string
  title: string
  detail: string
  instruction: string
  status: planned | running | succeeded | failed | cancelled | blocked
  result: string | null
  organizer_task_id: string | null

PlanRun
  plan_id: UUID
  flow_id: string | null
  revision: integer | null
  run_mode: next | all

AutoPlanDecision
  route: direct | plan
  draft: PlanDraft | null
```

## State transitions

```text
draft --select--> ready --run--> running --all steps succeed--> succeeded
                                |--step fails-------------> failed
                                |--step blocks------------> blocked
                                |--cancel-----------------> cancelled
```

- A plan becomes `ready` only after selecting one returned approach. That
  selection atomically binds the selected plan's live step identifiers to new
  Organizer task identifiers for the current session.
- A single failed/blocked step stops `Run all`; no later step is started.
- A cancelled run retains its previous result text for inspection but starts no
  further steps.
- The model never chooses a state transition; it supplies a draft and executes
  the user-selected step through OpenClaw.
