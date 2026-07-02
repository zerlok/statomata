# Task A: Mermaid diagram export for declarative state machines

Add a feature to the statomata library: export a `DeclarativeStateMachine` subclass as a
[Mermaid state diagram](https://mermaid.js.org/syntax/stateDiagram.html) string, so users
can visualize their state machines in docs, GitHub READMEs, and Mermaid Live.

## Requirements

1. Provide a public function or method that, given a `DeclarativeStateMachine` subclass
   (the class, not an instance), returns a `str` containing a valid `stateDiagram-v2`
   Mermaid diagram.
2. The diagram must include:
   - every state declared on the machine;
   - an initial-state marker (`[*] --> <initial>`);
   - final-state markers (`<final> --> [*]`) for states declared final;
   - one labeled edge per transition, labeled with the transition method's name.
3. If a transition method can lead to multiple destinations, emit one edge per
   source→destination pair.
4. Human-readable state titles: if a state was declared with a custom name/title, use it
   as the Mermaid state description; otherwise use the attribute name.
5. Decide yourself where the feature lives and how it is exposed (module, naming, whether
   it also hangs off the class); it must fit the library's existing layering and style.
6. Add unit tests covering at least: the `OpenCloseExample` from the README, a machine
   with a final state, and a machine where one method has multiple destination states.
   Assert on the exact rendered output.
7. Document the feature in `README.md` with a short example.
8. No new runtime dependencies.

## Constraints (from the repo's conventions — violations fail the task)

- Python 3.9 compatibility: no `X | Y` unions, and no `from __future__ import annotations`
  in new files (per CLAUDE.md). Heads-up: the existing `src/statomata` modules currently
  *do* start with `from __future__ import annotations`, but CLAUDE.md forbids it for new
  code — follow CLAUDE.md, not that legacy habit. Match the existing modules for
  everything else about typing (`t.Optional`/`t.Union`, `typing_extensions`, quoted
  forward refs).
- Must pass, with zero errors/warnings: `poetry run ruff format --check`,
  `poetry run ruff check`, `poetry run mypy`, `poetry run pytest`.
- Follow SSoT/DRY: derive the diagram from the machine's existing metadata — do not
  build a parallel representation of states/transitions.

## Definition of done

All four commands above pass; tests for the new feature exist and pass; README documents
the feature; working tree is committed on the current branch with a sensible message.
