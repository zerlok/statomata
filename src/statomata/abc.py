from __future__ import annotations

import abc
import typing as t

T_contra = t.TypeVar("T_contra", contravariant=True)
S_contra = t.TypeVar("S_contra", contravariant=True)
U_contra = t.TypeVar("U_contra", contravariant=True)
V_contra = t.TypeVar("V_contra", contravariant=True)
V_co = t.TypeVar("V_co", covariant=True)


class StateMachineError(Exception):
    pass


class StateMachineFinalStateReachedError(StateMachineError):
    pass


class StateMachine(t.Generic[U_contra, V_co], metaclass=abc.ABCMeta):
    """State Machine interface."""

    @abc.abstractmethod
    def run(self, /, income: U_contra) -> V_co:
        """
        Process incomes through the state machine states until the final state is reached, returns outcome from states.
        """
        raise NotImplementedError


class Context(t.Generic[T_contra], metaclass=abc.ABCMeta):
    """
    A context for states to control the state machine.

    Each `StateMachine` implementation must provide appropriate `Context` instance to `handle` method of `State`.
    """

    @abc.abstractmethod
    def set_state(self, state: T_contra) -> None:
        """Change StateMachine state."""
        raise NotImplementedError

    @abc.abstractmethod
    def set_finished(self, reason: str, *details: object) -> None:
        """Set final state, so StateMachine will stop run."""
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


class StateMachineSubscriber(t.Generic[S_contra, U_contra, V_contra], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def notify_start(self, state: S_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def notify_state_start(self, state: S_contra, income: U_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def notify_state_outcome(self, state: S_contra, income: U_contra, outcome: V_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def notify_state_finish(self, state: S_contra, income: U_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def notify_state_error(self, state: S_contra, error: Exception) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def notify_transition(self, source: S_contra, dest: S_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def notify_finish(self, state: S_contra) -> None:
        raise NotImplementedError


class StateMachineAsyncSubscriber(t.Generic[S_contra, U_contra, V_contra], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def notify_start(self, state: S_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def notify_state_start(self, state: S_contra, income: U_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def notify_state_outcome(self, state: S_contra, income: U_contra, outcome: V_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def notify_state_finish(self, state: S_contra, income: U_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def notify_state_error(self, state: S_contra, income: Exception) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def notify_transition(self, source: S_contra, dest: S_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def notify_finish(self, state: S_contra) -> None:
        raise NotImplementedError
