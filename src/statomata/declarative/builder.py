from __future__ import annotations

import abc
import inspect
import typing as t
from collections import OrderedDict
from functools import cached_property, wraps

from typing_extensions import ParamSpec, TypeAlias, override

P = ParamSpec("P")
T = t.TypeVar("T")
U_contra = t.TypeVar("U_contra", contravariant=True)
V_co = t.TypeVar("V_co", covariant=True)


# NOTE: base type helpers
MethodFuncAny: TypeAlias = t.Callable[..., object]  # type: ignore[explicit-any]
Fallback: TypeAlias = t.Union[type[Exception], t.Sequence[type[Exception]], bool]
Condition: TypeAlias = t.Union[t.Callable[[t.Any], bool], property]  # type: ignore[explicit-any]


class TransitionBuilder(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __call__(self, func: t.Callable[P, V_co]) -> t.Callable[P, V_co]:
        raise NotImplementedError

    @abc.abstractmethod
    def to(self, destination: State) -> Transition:
        raise NotImplementedError

    @abc.abstractmethod
    def when(self, condition: Condition) -> Transition:
        raise NotImplementedError

    @abc.abstractmethod
    def when_not(self, condition: Condition) -> Transition:
        raise NotImplementedError

    @abc.abstractmethod
    def ternary(self, condition: Condition) -> TernaryTransition:
        raise NotImplementedError


class StateRegistry:
    def __init__(self, states: t.Sequence[State]) -> None:
        self.__states = states

    @property
    def states(self) -> t.Sequence[State]:
        return self.__states

    @cached_property
    def initial(self) -> State:
        initials = list(state for state in self.__states if state.initial)

        if not initials:
            msg = "initial state is not set"
            raise ValueError(msg)

        if len(initials) > 1:
            msg = "initial state ambiguity"
            raise ValueError(msg, initials)

        return next(iter(initials))

    @cached_property
    def finals(self) -> t.Sequence[State]:
        finals = list(state for state in self.__states if state.final)

        if not finals:
            msg = "final state is not set"
            raise ValueError(msg)

        return finals

    @cached_property
    def fallbacks(self) -> t.Sequence[State]:
        return list(state for state in self.__states if state.fallback)


class TransitionRegistry(t.Iterable[tuple[MethodFuncAny, t.Sequence["Transition"]]]):
    def __init__(self) -> None:
        self.__funcs = OrderedDict[MethodFuncAny, list[Transition]]()

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented

        return other.__funcs == self.__funcs

    @override
    def __iter__(self) -> t.Iterator[tuple[MethodFuncAny, t.Sequence[Transition]]]:
        return iter(self.__funcs.items())

    def register(self, func: MethodFuncAny, method_def: Transition) -> None:
        if inspect.iscoroutinefunction(func):
            msg = "coroutine functions is not supported"
            # NOTE: inspect returns any
            raise TypeError(msg, func, method_def)  # type: ignore[misc]

        self.__funcs.setdefault(func, list[Transition]()).append(method_def)


class State(TransitionBuilder):
    def __init__(
        self,
        name: t.Optional[str] = None,
        initial: bool = False,
        final: bool = False,
        fallback: Fallback = False,
        transitions: t.Optional[TransitionRegistry] = None,
    ) -> None:
        self.name = name
        self.initial = initial
        self.final = final
        self.fallback = fallback
        self.transitions = transitions if transitions is not None else TransitionRegistry()

    @override
    def __str__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"

    @override
    def __call__(self, func: t.Callable[P, V_co]) -> t.Callable[P, V_co]:
        return self.to(self)(func)

    @override
    def to(self, destination: State) -> Transition:
        return Transition(self.transitions, self).to(destination)

    @override
    def when(self, condition: Condition) -> Transition:
        return Transition(self.transitions, self).when(condition)

    @override
    def when_not(self, condition: Condition) -> Transition:
        return Transition(self.transitions, self).when_not(condition)

    @override
    def ternary(self, condition: Condition) -> TernaryTransition:
        return Transition(self.transitions, self).ternary(condition)


class Transition(TransitionBuilder):
    def __init__(
        self,
        registry: TransitionRegistry,
        source: State,
        destination: t.Optional[State] = None,
        condition: t.Optional[Condition] = None,
    ) -> None:
        self.registry = registry
        self.source = source
        self.destination = destination
        self.condition = condition

    @override
    def __str__(self) -> str:
        return f"<{self.__class__.__name__}: {self.source} -> {self.destination}>"

    @override
    def __call__(self, func: t.Callable[P, V_co]) -> t.Callable[P, V_co]:
        # NOTE: `MethodFuncAny` is actually `t.Callable[..., t.Any]`
        self.registry.register(t.cast("MethodFuncAny", func), self)
        return func

    @override
    def to(self, destination: State) -> Transition:
        self.destination = destination
        return self

    @override
    def when(self, condition: Condition) -> Transition:
        self.condition = condition
        return self

    @override
    def when_not(self, condition: Condition) -> Transition:
        if isinstance(condition, property):  # type: ignore[misc]
            cond: t.Optional[t.Callable[[object], bool]] = condition.fget
            if cond is None:
                msg = "property fget method must be set"
                raise TypeError(msg, condition)

            @wraps(cond)
            def negate(obj: object) -> bool:
                return not cond(obj)

        else:

            @wraps(condition)
            def negate(obj: object) -> bool:
                return not condition(obj)

        return self.when(negate)

    @override
    def ternary(self, condition: Condition) -> TernaryTransition:
        return TernaryTransition(self.registry, self.source, condition)


class TernaryTransition:
    def __init__(
        self,
        registry: TransitionRegistry,
        source: State,
        condition: Condition,
    ) -> None:
        self.__condition = condition
        self.__then = Transition(registry, source).when(condition)
        self.__otherwise = Transition(registry, source).when_not(condition).to(source)

    def __call__(self, func: t.Callable[P, V_co]) -> t.Callable[P, V_co]:
        self.__then(func)
        self.__otherwise(func)

        return func

    def then(self, state: State) -> TernaryTransition:
        self.__then.to(state)
        return self

    def otherwise(self, state: State) -> TernaryTransition:
        self.__otherwise.to(state)
        return self
