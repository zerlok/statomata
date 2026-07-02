# Workflow: Warp plan + task lists (`warp-plan`) + control (`warp-plain`)

**Paradigm: plan-driven execution.** Warp's agent generates a persistent, human-editable
plan (`/plan` or natural language), automatically decomposes complex requests into a
tracked task list, executes steps sequentially with incremental file changes, and lets
the human revise the plan mid-run. No scripted orchestration, no parallel subagents in
this mode — the differentiator is the explicit, editable plan artifact and continuous
human-in-the-loop oversight.

Docs: [Agent planning](https://docs.warp.dev/agent-platform/capabilities/planning/),
[Task lists](https://docs.warp.dev/agent-platform/capabilities/task-lists/).

Warp is a desktop app — these runs happen interactively on your machine.

## Setup

Install Warp (https://www.warp.dev/download), sign in; Settings → AI → pick the same
model family as the `cc-*` runs and record it. Ensure the worktree has `WARP.md`
(copied from CLAUDE.md per the protocol).

## Launch — `warp-plan`

1. `cd ../statomata-runs/<task>-warp-plan`, open Warp there, enter Agent Mode.
2. First message — explicit plan trigger + verbatim spec:

```
/plan
<full contents of harness-eval/tasks/task-<X>-....md>
```

3. Approve the generated plan **without editing it** (editing is allowed by the
   paradigm, but for comparability the first run should measure the mechanism, not your
   plan-authoring; if you do a plan-edited variant, log it as `warp-plan-edited`).
4. Let it execute; interventions follow the standard rules.

## Launch — `warp-plain` (control)

Same setup; paste the task spec verbatim with no `/plan`. Warp auto-creates task lists
for complex requests and this cannot be fully disabled — if it does, let it, and record
that the control self-upgraded to task-list mode. That observation is a result in
itself (Warp has no true plain mode for complex tasks).

## Workflow-specific observables

- The plan artifact itself (copy into the results file) and the task list: step count,
  granularity, ordering quality — compare its decomposition against the phase structure
  `cc-dyn`/`omp-dyn` chose for the same task.
- Plan drift: did the agent revise the plan mid-run? Did steps get skipped/merged?
- Whether it ran the four check commands as plan steps or only when reminded.
- Approval friction: number of command-approval stops (record, but don't count as
  interventions).
- Cost/credits; paired delta vs `warp-plain`.

## Optional variant — Oz cloud agents (`warp-oz`)

Warp's autonomous cloud execution (push branch → Oz runs → PR). A third paradigm
(fire-and-forget autonomous) if you want it later; score the PR branch in a local
worktree like any other run.
