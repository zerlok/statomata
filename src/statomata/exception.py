from __future__ import annotations

import typing as t

from typing_extensions import override

from statomata.abc import StateMachineError

S = t.TypeVar("S")
T = t.TypeVar("T")


class StateMachineRuntimeError(StateMachineError, RuntimeError):
    """Raised when state machine run fails."""


class InvalidStateError(t.Generic[S, T], StateMachineRuntimeError):
    """Raised when state machine has invalid state to handle the provided income."""

    def __init__(
        self,
        actual: S,
        expected: t.Optional[t.Union[S, t.Collection[S]]] = None,
        message: t.Optional[str] = None,
    ) -> None:
        super().__init__()

        self.actual = actual
        self.expected = expected
        self.message = message

    @override
    def __str__(self) -> str:
        return f"message={self.message}; actual={self.actual}; expected={self.expected}"


class AbortedStateReachedError(StateMachineRuntimeError):
    """Raised when running state machine after the final state was reached."""
