# Task B: FSM state persistence (pluggable storage + builtin PostgreSQL)

Add state persistence to the statomata library: a way to save the current state of a
running state machine to durable storage and restore a machine from it later — so
long-lived workflows (order processing, sagas, chat sessions) can survive process
restarts.

## Requirements

1. **Pluggable storage interface.** Define an abstraction for persisting and loading a
   machine's current state, keyed by a caller-supplied machine identifier. Users must be
   able to implement custom storages (Redis, filesystem, ORM, ...) against this interface
   without touching library internals. Support both sync and async usage in a way
   consistent with how the library already splits sync/async.
2. **Persist on transition.** State changes are saved automatically as the machine runs.
   Design hint, not a mandate: the library already has a `StateMachineSubscriber`
   notification mechanism — evaluate whether it is the right seam before inventing a
   new one.
3. **Restore.** Given a machine identifier and a storage, a user can create/start a
   machine in the persisted state instead of the initial state. Decide and document the
   behaviour when no persisted state exists (fresh start) and when the persisted state
   name no longer exists on the machine (error).
4. **What gets persisted:** at minimum the current state's identity, and enough metadata
   to make restoration safe (e.g. a machine-type or version discriminator is up to your
   design). You do NOT need to serialize in-flight incomes, deferred queues, or arbitrary
   user attributes — scope is current-state persistence. Document this boundary
   explicitly.
5. **Builtin in-memory storage** — used in unit tests and as a reference implementation.
6. **Builtin PostgreSQL storage.**
   - The Postgres driver must be an optional dependency (poetry extra, like the existing
     `anyio` extra) — `pip install statomata` must stay dependency-free and importing the
     core library must not require the driver.
   - Choose the driver and schema yourself; the storage must create its table if missing
     (or document the DDL) and be safe for concurrent machines with distinct identifiers.
   - Integration tests for the Postgres storage must be skipped cleanly when no database
     is available; use an env var (e.g. `STATOMATA_TEST_POSTGRES_DSN`) to opt in. Do not
     make the default `pytest` run require Docker or a running database.
7. Works for both the declarative API (`DeclarativeStateMachine`) and at least one
   low-level automaton kind (e.g. unary). Declarative states must be identifiable by a
   stable string name.
8. Add unit tests (in-memory storage) covering: save-on-transition, restore-to-saved
   state, fresh start when nothing persisted, unknown-state error case.
9. Document the feature in `README.md`: a short example with the in-memory storage and a
   note on the Postgres extra.

## Constraints (from the repo's conventions — violations fail the task)

- Python 3.9 compatibility: no `X | Y` unions, and no `from __future__ import annotations`
  in new files (per CLAUDE.md). Heads-up: the existing `src/statomata` modules currently
  *do* start with `from __future__ import annotations`, but CLAUDE.md forbids it for new
  code — follow CLAUDE.md, not that legacy habit. Match the existing modules' typing style
  otherwise (`t.Optional`/`t.Union`, `typing_extensions`, quoted forward refs).
- Must pass, with zero errors/warnings: `poetry run ruff format --check`,
  `poetry run ruff check`, `poetry run mypy`, `poetry run pytest` (without a database
  running).
- Keep the core dependency-free: persistence interfaces must not import the Postgres
  driver at module level anywhere the core imports.
- Follow SSoT/DRY and the existing layering (abc → executor → shells → sdk/declarative).

## Definition of done

All four commands above pass with no database running; the Postgres storage exists
behind an extra with opt-in integration tests; README documents the feature; working
tree is committed on the current branch with a sensible message.
