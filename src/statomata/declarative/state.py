# NOTE: ignore any usage in this module, otherwise it's hard to define types for callables
# mypy: disable-error-code="misc, explicit-any"

from __future__ import annotations

import abc
import typing as t
from collections import defaultdict
from dataclasses import dataclass

from typing_extensions import override

from statomata.unary import UnaryState

if t.TYPE_CHECKING:
    from statomata.abc import Context


K = t.TypeVar("K", bound=t.Hashable)
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


class MethodCallTransition(t.Generic[T], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def perform(self, container: T, context: Context[MethodCallState[T]]) -> bool:
        raise NotImplementedError


class ConstantMethodCallTransition(t.Generic[T], MethodCallTransition[T]):
    def __init__(self, destination: MethodCallState[T]) -> None:
        self.__destination = destination

    @override
    def perform(self, container: T, context: Context[MethodCallState[T]]) -> bool:
        context.set_state(self.__destination, final=self.__destination.final)
        return True


class ConditionalMethodCallTransition(t.Generic[T], MethodCallTransition[T]):
    def __init__(
        self,
        condition: t.Callable[[T], bool],
        then: MethodCallState[T],
        otherwise: t.Optional[MethodCallState[T]] = None,
    ) -> None:
        self.__condition = condition
        self.__then = then
        self.__otherwise = otherwise

    @override
    def perform(self, container: T, context: Context[MethodCallState[T]]) -> bool:
        if self.__condition(container):
            context.set_state(self.__then, final=self.__then.final)
            return True

        if self.__otherwise is not None:
            context.set_state(self.__otherwise, final=self.__otherwise.final)
            return True

        return False


class KeyMappingMethodCallTransition(t.Generic[K, T], MethodCallTransition[T]):
    def __init__(
        self,
        key: t.Callable[[T], K],
        destinations: t.Mapping[K, MethodCallState[T]],
        default: t.Optional[MethodCallState[T]] = None,
    ) -> None:
        self.__key = key
        self.__destinations = destinations
        self.__default = default

    @override
    def perform(self, container: T, context: Context[MethodCallState[T]]) -> bool:
        key = self.__key(container)
        destination = self.__destinations.get(key, self.__default)

        if destination is not None:
            context.set_state(destination, final=destination.final)
            return True

        return False


class MethodCallState(t.Generic[T], UnaryState[MethodCall[T, object], object]):
    """
    Executes provided method function and switches to appropriate state using set transitions.

    Method `handle` returns the same value returned from invoked `func`. The provided `func` must be an unbound method
    of `DeclarativeStateMachine` class.

    State chooses the first transition with truthy condition.
    """

    def __init__(self, *, name: str, initial: bool, final: bool) -> None:
        self.__name = name
        self.__initial = initial
        self.__final = final
        self.__transitions = defaultdict[t.Callable[..., object], list[MethodCallTransition[T]]](list)

    @override
    def __str__(self) -> str:
        return f"<{self.__class__.__name__} at {hex(id(self))}: {self.__name}>"

    __repr__ = __str__

    @override
    def handle(
        self,
        income: MethodCall[T, V_co],
        context: Context[MethodCallState[T]],
    ) -> V_co:
        transitions = self.__transitions[income.func]

        outcome = income.func(income.container, *income.args, **income.kwargs)

        for transition in transitions:
            if transition.perform(income.container, context):
                break

        return outcome

    @property
    def name(self) -> str:
        return self.__name

    @property
    def initial(self) -> bool:
        return self.__initial

    @property
    def final(self) -> bool:
        return self.__final

    def add_transitions(self, func: t.Callable[..., object], *transitions: MethodCallTransition[T]) -> None:
        self.__transitions[func].extend(transitions)
