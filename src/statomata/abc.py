from __future__ import annotations

import abc
import typing as t

from typing_extensions import override

S_contra = t.TypeVar("S_contra", contravariant=True)
S_co = t.TypeVar("S_co", covariant=True)
U_contra = t.TypeVar("U_contra", contravariant=True)
V_contra = t.TypeVar("V_contra", contravariant=True)
V_co = t.TypeVar("V_co", covariant=True)


class StateMachineError(Exception):
    """Base exception for statomata package."""


class StateMachineRuntimeError(StateMachineError, RuntimeError):
    """Raised when state machine run fails."""


class InvalidStateError(t.Generic[U_contra, V_co], StateMachineRuntimeError):
    """Raised when state machine has invalid state to handle the provided income."""

    def __init__(self, actual: State[U_contra, V_co], expected: t.Optional[State[U_contra, V_co]] = None) -> None:
        self.actual = actual
        self.expected = expected

    @override
    def __str__(self) -> str:
        return f"actual={self.actual}; expected={self.expected}"


class FinalStateAlreadyReachedError(StateMachineRuntimeError):
    """Raised when state machine execution is triggered again after the final state was reached."""


class Context(t.Generic[S_contra], metaclass=abc.ABCMeta):
    """
    A context for states to control the state machine.

    Each `StateMachine` implementation must provide appropriate `Context` instance to `handle` method of `State`.
    """

    @abc.abstractmethod
    def set_state(self, state: S_contra) -> None:
        """Change `StateMachine` state."""
        raise NotImplementedError

    @abc.abstractmethod
    def set_final_state(self, reason: str, *details: object) -> None:
        """Set final state, `StateMachine` will stop run."""
        raise NotImplementedError


class State(t.Generic[U_contra, V_co], metaclass=abc.ABCMeta):
    """
    State interface.

    State may manipulate the running `StateMachine` via `Context` transitions.

    State handles income and returns the outcome.
    """

    @abc.abstractmethod
    def handle(self, income: U_contra, context: Context[State[U_contra, V_co]]) -> V_co:
        """
        Handles provided income, manipulates the context and returns the outcome.

        States can:
            - Return outcomes while processing the income
            - Change the state using `context.set_state`
            - Signal to finish the StateMachine run using `context.set_finished`
            - Enqueue or requeue incomes using `context.enqueue` and `context.requeue`
        """
        raise NotImplementedError


class StateMachine(t.Generic[S_co], metaclass=abc.ABCMeta):
    """
    State machine interface.

    Each implementation should provide public transitions to process incomes through states until the final state is
    reached and return outcomes from states.
    """

    @property
    @abc.abstractmethod
    def current_state(self) -> S_co:
        """Provide current state."""
        raise NotImplementedError


class StateMachineSubscriber(t.Generic[S_contra, U_contra, V_contra], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def notify_started(self, state: S_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def notify_state_entered(self, state: S_contra, income: U_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def notify_state_outcome(self, state: S_contra, income: U_contra, outcome: V_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def notify_state_left(self, state: S_contra, income: U_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def notify_state_failed(self, state: S_contra, error: Exception) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def notify_transitioned(self, source: S_contra, dest: S_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def notify_finished(self, state: S_contra) -> None:
        raise NotImplementedError


class StateMachineAsyncSubscriber(t.Generic[S_contra, U_contra, V_contra], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def notify_started(self, state: S_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def notify_state_entered(self, state: S_contra, income: U_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def notify_state_outcome(self, state: S_contra, income: U_contra, outcome: V_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def notify_state_left(self, state: S_contra, income: U_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def notify_state_failed(self, state: S_contra, income: Exception) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def notify_transitioned(self, source: S_contra, dest: S_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def notify_finished(self, state: S_contra) -> None:
        raise NotImplementedError
