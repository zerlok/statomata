# CLAUDE.md

Read `README.md` first.

## Conventions

- Follow principles: SSoT, DRY.
- Python 3.9 floor: no `X | Y`, `type X = ...`, `class Genric[T]: ...`.
- Ultra strict mypy + near-all ruff rules. If you need to `t.cast` or `t.Any` or `# noqa`, then always add explanation comment `# NOTE: why we have to do it so`.
