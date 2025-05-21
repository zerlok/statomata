from __future__ import annotations

import abc
import typing as t
from collections import defaultdict

from typing_extensions import override

if t.TYPE_CHECKING:
    from statomata.abc import Context

K = t.TypeVar("K", bound=t.Hashable)
U_contra = t.TypeVar("U_contra", contravariant=True)
S_contra = t.TypeVar("S_contra", contravariant=True)
S_co = t.TypeVar("S_co", covariant=True)


class Transition(t.Generic[U_contra, S_contra], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def perform(self, income: U_contra, context: Context[S_contra]) -> bool:
        raise NotImplementedError


class AsyncTransition(t.Generic[U_contra, S_contra], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def perform(self, income: U_contra, context: Context[S_contra]) -> bool:
        raise NotImplementedError


class ConstantTransition(t.Generic[U_contra, S_contra], Transition[U_contra, S_contra]):
    def __init__(self, destination: S_contra) -> None:
        self.__destination = destination

    @override
    def __str__(self) -> str:
        return f"<{self.__class__.__name__} at {hex(id(self))}: {self.__destination}>"

    @override
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__destination!r})"

    @override
    def perform(self, income: U_contra, context: Context[S_contra]) -> bool:
        context.set_state(self.__destination)
        return True


class ConditionalTransition(t.Generic[U_contra, S_contra], Transition[U_contra, S_contra]):
    def __init__(
        self,
        condition: t.Callable[[U_contra], bool],
        then: S_contra,
        otherwise: t.Optional[S_contra] = None,
    ) -> None:
        self.__condition = condition
        self.__then = then
        self.__otherwise = otherwise

    @override
    def __str__(self) -> str:
        return f"<{self.__class__.__name__} at {hex(id(self))}: {self.__condition}>"

    @override
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"condition={self.__condition!r}, "
            f"then={self.__then!r}, "
            f"otherwise={self.__otherwise!r}"
            ")"
        )

    @override
    def perform(self, income: U_contra, context: Context[S_contra]) -> bool:
        if self.__condition(income):
            context.set_state(self.__then)
            return True

        if self.__otherwise is not None:
            context.set_state(self.__otherwise)
            return True

        return False


class MappingTransition(t.Generic[K, U_contra, S_contra], Transition[U_contra, S_contra]):
    def __init__(
        self,
        key: t.Callable[[U_contra], K],
        destinations: t.Mapping[K, S_contra],
        default: t.Optional[S_contra] = None,
    ) -> None:
        self.__key = key
        self.__destinations = destinations
        self.__default = default

    @override
    def __str__(self) -> str:
        return f"<{self.__class__.__name__} at {hex(id(self))}: {self.__key}>"

    @override
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"key={self.__key!r}, "
            f"destinations={self.__destinations!r}, "
            f"default={self.__default!r}"
            ")"
        )

    @override
    def perform(self, income: U_contra, context: Context[S_contra]) -> bool:
        key = self.__key(income)
        destination: t.Optional[S_contra] = self.__destinations.get(key, self.__default)

        if destination is not None:
            context.set_state(destination)
            return True

        return False


class Sync2AsyncTransitionAdapter(t.Generic[U_contra, S_contra], AsyncTransition[U_contra, S_contra]):
    def __init__(self, inner: Transition[U_contra, S_contra]) -> None:
        self.__inner = inner

    @override
    async def perform(self, income: U_contra, context: Context[S_contra]) -> bool:
        return self.__inner.perform(income, context)


class TransitionExecutor(t.Generic[K, U_contra, S_co]):
    def __init__(
        self,
        transitions: t.Optional[t.Mapping[K, t.Sequence[Transition[U_contra, S_co]]]] = None,
    ) -> None:
        self.__transitions = defaultdict[K, list[Transition[U_contra, S_co]]](list)

        for tr_key, tr_values in (transitions or {}).items():
            self.add_transitions(tr_key, *tr_values)

    def execute(self, key: K, income: U_contra, context: Context[S_co]) -> t.Optional[Transition[U_contra, S_co]]:
        transitions = self.__transitions[key]

        for transition in transitions:
            if transition.perform(income, context):
                return transition

        return None

    def add_transitions(self, key: K, *values: Transition[U_contra, S_co]) -> None:
        self.__transitions[key].extend(values)


class AsyncTransitionExecutor(t.Generic[K, U_contra, S_co]):
    def __init__(
        self,
        transitions: t.Optional[t.Mapping[K, t.Sequence[AsyncTransition[U_contra, S_co]]]] = None,
    ) -> None:
        self.__transitions = defaultdict[K, list[AsyncTransition[U_contra, S_co]]](list)

        for tr_key, tr_values in (transitions or {}).items():
            self.add_transitions(tr_key, *tr_values)

    async def execute(
        self,
        key: K,
        income: U_contra,
        context: Context[S_co],
    ) -> t.Optional[AsyncTransition[U_contra, S_co]]:
        transitions = self.__transitions[key]

        for transition in transitions:
            ok = await transition.perform(income, context)
            if ok:
                return transition

        return None

    def add_transitions(self, key: K, *values: AsyncTransition[U_contra, S_co]) -> None:
        self.__transitions[key].extend(values)
