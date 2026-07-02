# Run: <task>-<workflow>[-<n>]

## Run metadata

- date:
- workflow ID (cc-dyn / cc-plain / omp-dyn / omp-plain / warp-plan / warp-plain / ...):
- harness + version:
- model (pin exactly — cross-run comparability depends on it):
- trigger used (exact phrase / slash command):
- wall-clock (start → end):
- tokens / cost:
- human interventions (count + list each one):

## Workflow observations

- **Decomposition**: how did the mechanism split the task? (phases / plan steps / task
  list / none). Copy the artifact — orchestration script, plan text, task list — here.
- **Parallelism**: subagent count, what ran concurrently, model routing if any.
- **Self-verification**: was there a verify/review stage? Did it catch real defects?
  Did the agent run the four check commands unprompted?
- **Intermediate artifacts**: scripts, plans, specs, journals produced along the way.
- **Failure handling / resume**: retries, journaled resumes, dead ends, derailments.
- **Human-in-the-loop shape**: where could you intervene, and where did you have to?
- **Convention adherence**: respected CLAUDE/AGENTS/WARP.md constraints (py3.9 unions,
  strict typing, noqa comments) unprompted?

## Rubric (0 = missing/violated, 1 = partial, 2 = solid)

| dimension | score | notes |
|-----------|-------|-------|
| API design fits existing layering (abc/executor/shells/declarative) | | |
| Scoping discipline (built what was asked, no sprawl) | | |
| Python 3.9 + typing conventions respected without reminders | | |
| Test quality (edge cases from spec, meaningful asserts) | | |
| Docs (README example accurate and runnable) | | |
| Dependency hygiene (Task B: extra isolation; Task A: zero deps) | | |
| Commit quality (committed, sensible message, no junk files) | | |
**Rubric total: /14**

## Paired delta (fill once the matching control/workflow run is scored)

| metric | this run | paired run | delta |
|--------|----------|------------|-------|
| gates passed (0–4) | | | |
| rubric total | | | |
| cost | | | |
| wall-clock | | | |
| interventions | | | |

## Verdict

<!-- one paragraph: would you merge this PR, and did the workflow mechanism earn its
overhead relative to the paired run? -->
