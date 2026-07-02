# Workflow Evaluation: agentic execution workflows on statomata

An experiment comparing **execution workflows** — the orchestration mechanisms coding
agents provide — on identical, real tasks in this library. The unit of comparison is the
workflow paradigm, **not** the harness product. Every workflow run is paired with a
plain single-agent-loop run in the same harness, so the workflow's contribution can be
separated from the harness/model it happens to run in.

## Workflow paradigms under test

| ID | Workflow | Paradigm | Harness (control variable) | Docs |
|----|----------|----------|---------------------------|------|
| `cc-dyn` | Claude Code dynamic workflows | **Scripted orchestration**: model authors a deterministic JS script; subagent fan-out/pipeline, schema-validated outputs, verify stages, journaled resume | Claude Code | [workflows/claude-dynamic-workflows.md](workflows/claude-dynamic-workflows.md) |
| `omp-dyn` | pi-dynamic-workflows | **Scripted orchestration** — same paradigm ported to Pi/oh-my-pi (code-mode subagents, model routing, worktree isolation, journaled resume) | oh-my-pi | [workflows/omp-dynamic-workflows.md](workflows/omp-dynamic-workflows.md) |
| `warp-plan` | Warp plan + task lists | **Plan-driven execution**: model-generated editable plan (`/plan`), automatic task-list decomposition, sequential execution with human-in-the-loop plan revision | Warp | [workflows/warp-plan.md](workflows/warp-plan.md) |
| `cc-plain` | — (control) | Single agent loop, no orchestration opt-in | Claude Code | trivial: just paste the task |
| `omp-plain` | — (control) | Single agent loop, keyword trigger off | oh-my-pi | see omp doc §controls |
| `warp-plain` | — (control) | Agent mode with task-list auto-decomposition suppressed as far as Warp allows (note: Warp may auto-plan anyway — record it) | Warp | see warp doc §controls |

Optional fifth paradigm if appetite remains: **spec-driven workflow** (OpenSpec `opsx:
propose → apply → archive`, installed here) — artifact-first with human gates between
phases. It is harness-agnostic, which makes it a nice bridge datapoint (`cc-spec`).

### What this design can answer

1. **Paradigm effect** (within-harness pairs): does scripted orchestration beat a plain
   loop on the same task, same harness, same model? (`cc-dyn` vs `cc-plain`,
   `omp-dyn` vs `omp-plain`.) Does plan-driven beat plain? (`warp-plan` vs `warp-plain`.)
2. **Implementation effect** (same paradigm, two implementations): `cc-dyn` vs `omp-dyn`
   — the original vs its port. Differences here are implementation quality, not paradigm.
3. **Paradigm characterization** (qualitative): how each mechanism decomposes work, what
   it parallelizes, whether it verifies its own output, what intermediate artifacts it
   produces (scripts, plans, task lists, specs), how it handles resume/failure, and where
   humans can intervene.

Cross-harness *score* comparisons (e.g. `cc-dyn` vs `warp-plan` gate results) are
confounded by model and harness differences — treat them as descriptive, not causal.
Pin the same model family everywhere it's configurable and record it per run.

## Tasks (the workload — held constant)

| ID | Task | Why it stresses workflows | Spec |
|----|------|---------------------------|------|
| `A` | Mermaid diagram export for declarative state machines | Bounded, well-specified — measures whether orchestration adds value or just overhead when a plain loop suffices | [tasks/task-a-mermaid-export.md](tasks/task-a-mermaid-export.md) |
| `B` | FSM state persistence (storage interface + builtin Postgres) | Design-heavy, decomposable (interface / in-memory / postgres / tests / docs), benefits from parallel exploration and a verify stage — where workflow paradigms should differentiate | [tasks/task-b-state-persistence.md](tasks/task-b-state-persistence.md) |

Hypothesis worth writing down before running: workflows win on B, tie or lose (on cost)
on A.

## Protocol

One run = one (task, workflow) pair. Core grid = 2 tasks × 6 workflows = 12 runs.
If budget-constrained, prioritize Task B across all six, then Task A on
`cc-dyn`/`cc-plain`/`warp-plan`/`warp-plain`.

### 1. Prepare a worktree per run

```bash
cd ~/dev/statomata
git worktree add ../statomata-runs/<task>-<workflow> -b eval/<task>-<workflow> main
cd ../statomata-runs/<task>-<workflow>
poetry install -E anyio
```

### 2. Equalize project instructions

Harnesses read different context files (`CLAUDE.md` / `AGENTS.md` / `WARP.md`). In each
worktree:

```bash
cp CLAUDE.md AGENTS.md && cp CLAUDE.md WARP.md
```

### 3. Run

Give the workflow **exactly** the task spec contents as the prompt, plus only the
minimal trigger phrase the mechanism requires (documented per workflow in `workflows/`).
The trigger is part of the treatment; everything else must be identical.

Intervention rules (same for all runs):
- Answer design questions only with "your call, follow the spec" — and count it.
- Accepting permission prompts is not an intervention; steering is.
- Let derailed runs finish; score what exists and note the derailment.

Record during the run: wall-clock, tokens/cost, interventions, and the
workflow-specific observables listed in the results template (decomposition shape,
parallelism, verification behaviour, intermediate artifacts, resume events).

### 4. Score

```bash
./harness-eval/score.sh ../statomata-runs/<task>-<workflow> <task>-<workflow>
```

Writes objective gates (`ruff format --check`, `ruff check`, `mypy`, `pytest`), diff
stats, and test delta to `harness-eval/results/<task>-<workflow>.md`; then fill in the
rubric and workflow-observation sections (template: [results/TEMPLATE.md](results/TEMPLATE.md)).

### 5. Analyze

Per paradigm question above:
- **Paired deltas**: for each harness, workflow-run minus plain-run on gates passed,
  rubric total, cost, wall-clock, interventions. This is the headline table.
- **Implementation comparison**: `cc-dyn` vs `omp-dyn` — orchestration script shape,
  subagent counts, verify-stage effectiveness, resume robustness, cost accounting.
- **Paradigm writeup**: one section per paradigm describing observed decomposition,
  parallelism, self-verification, artifacts, and failure modes — grounded in the
  per-run behaviour notes.

## Ground rules

- Never run anything in the main checkout — worktrees only, one run per worktree.
- `harness-eval/` and `../statomata-runs/` stay out of library commits (already in
  `.git/info/exclude`).
- Write down model + version for every run; a workflow comparison with drifting models
  is a model comparison.
