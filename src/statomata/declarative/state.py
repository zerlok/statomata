# NOTE: ignore any usage in this module, otherwise it's hard to define types for callables
# mypy: disable-error-code="misc, explicit-any"

from __future__ import annotations

import typing as t
from collections import defaultdict
from dataclasses import dataclass

from typing_extensions import override

from statomata.unary import UnaryState

if t.TYPE_CHECKING:
    from statomata.abc import Context

T = t.TypeVar("T")
V_co = t.TypeVar("V_co", covariant=True)


# NOTE: PramSpec doesn't work here
@dataclass(frozen=True)
class MethodCall(t.Generic[T, V_co]):
    container: T
    """An instance of `DeclarativeStateMachine` class."""

    func: t.Callable[..., V_co]
    """An unbound method of `DeclarativeStateMachine` class."""

    args: t.Sequence[object]
    kwargs: t.Mapping[str, object]


# NOTE: ParamSpec doesn't work here
@dataclass(frozen=True)
class MethodCallTransition(t.Generic[T]):
    func: t.Callable[..., object]
    """A method of `DeclarativeStateMachine` class the transition is associated with."""

    condition: t.Callable[[T], bool]
    """Check if transition to specified `destination` should be performed."""

    destination: MethodCallState[T]


class MethodCallState(t.Generic[T], UnaryState[MethodCall[T, object], object]):
    """
    Executes provided method function and switches to appropriate state using set transitions.

    Method `handle` returns the same value returned from invoked `func`. The provided `func` must be an unbound method
    of `DeclarativeStateMachine` class.

    State chooses the first transition with truthy condition.
    """

    def __init__(
        self,
        name: t.Optional[str] = None,
        transitions: t.Optional[t.Sequence[MethodCallTransition[T]]] = None,
    ) -> None:
        self.__name = name
        self.__transitions = defaultdict[t.Callable[..., object], list[MethodCallTransition[T]]](list)

        for transition in transitions or ():
            self.add_transition(transition)

    @override
    def __str__(self) -> str:
        return f"<{self.__class__.__name__} at {hex(id(self))}: {self.__name}>"

    @override
    def handle(
        self,
        income: MethodCall[T, V_co],
        context: Context[MethodCallState[T]],
    ) -> V_co:
        transitions = self.__transitions[income.func]

        outcome = income.func(income.container, *income.args, **income.kwargs)

        for transition in transitions:
            if transition.condition(income.container):
                context.set_state(transition.destination)
                break

        return outcome

    def add_transition(self, transition: MethodCallTransition[T]) -> None:
        self.__transitions[transition.func].append(transition)
