# mypy: disable-error-code="misc, explicit-any"

from __future__ import annotations

import typing as t
from collections import defaultdict
from dataclasses import dataclass

from typing_extensions import ParamSpec, override

from statomata.abc import Context
from statomata.unary import UnaryState

P = ParamSpec("P")
T = t.TypeVar("T")
V_co = t.TypeVar("V_co", covariant=True)


# NOTE: PramSpec doesn't work here
@dataclass(frozen=True)  # type: ignore[misc]
class MethodCall(t.Generic[T, V_co]):  # type: ignore[misc,explicit-any]
    container: T
    func: t.Callable[..., V_co]  # type: ignore[explicit-any]
    args: t.Sequence[object]
    kwargs: t.Mapping[str, object]


# NOTE: ParamSpec doesn't work here
@dataclass(frozen=True)  # type: ignore[misc]
class MethodCallTransition(t.Generic[T]):  # type: ignore[misc,explicit-any]
    func: t.Callable[..., object]  # type: ignore[explicit-any]
    condition: t.Callable[[T], bool]
    destination: MethodCallState[T]


class MethodCallState(t.Generic[T], UnaryState[MethodCall[T, object], object]):
    def __init__(
        self,
        name: str,
        transitions: t.Optional[t.Sequence[MethodCallTransition[T]]] = None,
    ) -> None:
        self.__name = name
        self.__transitions = defaultdict[t.Callable[..., V_co], list[MethodCallTransition[T]]](list)  # type: ignore[misc]

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
        transitions = self.__transitions[income.func]  # type: ignore[misc,index]

        outcome = income.func(income.container, *income.args, **income.kwargs)

        for transition in transitions:
            if transition.condition(income.container):
                context.set_state(transition.destination)
                break

        return outcome

    def add_transition(self, transition: MethodCallTransition[T]) -> None:
        self.__transitions[transition.func].append(transition)  # type: ignore[misc,index]
