# Workflow: Claude Code dynamic workflows (`cc-dyn`) + control (`cc-plain`)

**Paradigm: scripted orchestration.** On opt-in, the model authors a deterministic
JavaScript orchestration script (phases, `agent()` fan-out, `pipeline()`, schema-validated
subagent outputs, verify stages) and executes it; runs are journaled and resumable, with
live progress in `/workflows`.

## Setup

Nothing to install. In the run worktree:

```bash
cd ../statomata-runs/<task>-cc-dyn
claude
```

Record `claude --version` and the session model.

## Launch — `cc-dyn`

First and only prompt (trigger phrase + verbatim spec):

```
Use a workflow to orchestrate this.

<full contents of harness-eval/tasks/task-<X>-....md>
```

"Use a workflow" is the explicit opt-in; without it the Workflow tool is not used.
(`ultracode` is a heavier standing opt-in — if you test it, log it as a separate variant
`cc-ultra`, not as `cc-dyn`.)

## Launch — `cc-plain` (control)

Identical setup, but the prompt is the task spec verbatim with **no** trigger phrase.
If Claude spontaneously proposes a workflow, decline and note it. Same model, same
worktree recipe.

## Workflow-specific observables

- The orchestration script itself (persisted under the session dir — save a copy into
  the results file): phase structure, fan-out width, barriers vs pipeline.
- Subagent count, what ran in parallel, per-phase purpose (explore / implement / verify).
- Whether a verify/review stage existed and whether it caught real defects.
- Resume events: did anything fail and get resumed via the journal?
- `/cost` totals — the paired delta against `cc-plain` is the headline number.
