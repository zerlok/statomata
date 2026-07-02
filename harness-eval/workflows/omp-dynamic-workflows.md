# Workflow: pi-dynamic-workflows on oh-my-pi (`omp-dyn`) + control (`omp-plain`)

**Paradigm: scripted orchestration — the same paradigm as `cc-dyn`, ported to Pi.**
[pi-dynamic-workflows](https://github.com/QuintinShaw/pi-dynamic-workflows) brings
Claude Code–style dynamic workflows to Pi/oh-my-pi: code-mode subagents with model
routing, journaled resume, git-worktree isolation, cost accounting, an interactive
`/workflows` TUI, and an `/ultracode` standing opt-in.

The `cc-dyn` vs `omp-dyn` pair is the implementation comparison: same paradigm, original
vs port. Differences observed here are implementation quality, not paradigm.

## Setup

```bash
bun install -g @oh-my-pi/pi-coding-agent   # oh-my-pi itself
# install the pi-dynamic-workflows extension per its README:
#   https://github.com/QuintinShaw/pi-dynamic-workflows
```

Pin and record versions of both (`omp --version`, extension version). Configure the
provider to the **same model family used in the `cc-*` runs** — this pair is only
meaningful if the model is held constant.

## Launch — `omp-dyn`

```bash
cd ../statomata-runs/<task>-omp-dyn
omp
```

First prompt — explicit trigger + verbatim spec:

```
/workflows run <full contents of harness-eval/tasks/task-<X>-....md>
```

(Alternatively the keyword trigger — the word "workflow" in a message — forces one; use
the explicit `/workflows run` form so the trigger is unambiguous and reproducible.)

## Launch — `omp-plain` (control)

Same setup, task spec verbatim as the first prompt, **no** slash command, and make sure
the extension's keyword trigger is disabled (or the extension not loaded) so the plain
loop is genuinely plain. Note which of the two you did — extension disabled is the
cleaner control, since merely having it installed may alter the system prompt.

## Workflow-specific observables

- The generated workflow script (the extension journals runs — copy the script into the
  results file): phase structure, fan-out width, subagent count.
- Model routing decisions (does it route subagents to cheaper models?).
- Worktree isolation behaviour — does it nest worktrees inside our eval worktree?
  Note any friction; that interaction is itself a finding.
- Verify stages and whether they caught real defects; resume events.
- Cost accounting output — compare with `omp-plain` for the paired delta, and with
  `cc-dyn` for the implementation comparison.
