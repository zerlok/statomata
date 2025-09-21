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

    Each `StateMachine` implementation must provide a `Context` instance to the `handle` method of a `State`. The
    context lets states manipulate execution flow: changing states, deferring incomes, recalling them later,
    or aborting the machine.
    """

    @abc.abstractmethod
    def set_state(self, state: S_contra, *, final: bool = False) -> None:
        """
        Change the state machine to the given state.

        :param state: the next state of the machine
        :param final: if True, transition to the new state and then abort
        """
        raise NotImplementedError

    @abc.abstractmethod
    def defer(self) -> None:
        """
        Defer the currently handled income.

        The income will be stored by the state machine for later recall.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def recall(self) -> None:
        """
        Recall one previously deferred income.

        On the next step, the state machine will call the current state's `handle` method with that income (if
        available).
        """
        raise NotImplementedError

    @abc.abstractmethod
    def abort(self) -> None:
        """
        Abort the state machine run.

        No further incomes will be processed after this call.
        """
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
    def notify_income_deferred(self, state: S_contra, income: U_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def notify_income_recalled(self, state: S_contra, income: U_contra) -> None:
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
    async def notify_income_deferred(self, state: S_contra, income: U_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def notify_income_recalled(self, state: S_contra, income: U_contra) -> None:
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
