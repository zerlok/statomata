from __future__ import annotations

import abc
import typing as t

S_contra = t.TypeVar("S_contra", contravariant=True)
S_co = t.TypeVar("S_co", covariant=True)
U_contra = t.TypeVar("U_contra", contravariant=True)
V_contra = t.TypeVar("V_contra", contravariant=True)
V_co = t.TypeVar("V_co", covariant=True)


class StateMachineError(Exception):
    """Base exception for statomata package."""


class Context(t.Generic[S_contra], metaclass=abc.ABCMeta):
    """
    A context for states to control the state machine.

    Each `StateMachine` implementation must provide appropriate `Context` instance to `handle` method of `State`.
    """

    @abc.abstractmethod
    def set_state(self, state: S_contra, *, final: bool = False) -> None:
        """Change `StateMachine` state. If final is set - abort the context."""
        raise NotImplementedError

    @abc.abstractmethod
    def abort(self) -> None:
        """Stop running the state machine. Means that the final state was reached."""
        raise NotImplementedError


class State(t.Generic[U_contra, V_co], metaclass=abc.ABCMeta):
    """
    State interface.

    State may manipulate the running `StateMachine` via `Context` methods.

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

    Each implementation should provide public methods to process incomes through states until the final state is
    reached and return outcomes from states.
    """

    @property
    @abc.abstractmethod
    def current_state(self) -> S_co:
        """Return current state."""
        raise NotImplementedError


class StateMachineSubscriber(t.Generic[S_contra, U_contra, V_contra], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def notify_initial(self, state: S_contra) -> None:
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
    def notify_transition(self, source: S_contra, destination: S_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def notify_final(self, state: S_contra) -> None:
        raise NotImplementedError


class AsyncStateMachineSubscriber(t.Generic[S_contra, U_contra, V_contra], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def notify_initial(self, state: S_contra) -> None:
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
    async def notify_transition(self, source: S_contra, destination: S_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def notify_final(self, state: S_contra) -> None:
        raise NotImplementedError
