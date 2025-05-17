from __future__ import annotations

import abc
import inspect
import typing as t
from collections import OrderedDict, defaultdict
from functools import cached_property, wraps

from typing_extensions import Concatenate, ParamSpec, TypeAlias, override

P = ParamSpec("P")
T = t.TypeVar("T")
V_co = t.TypeVar("V_co", covariant=True)
W_co = t.TypeVar("W_co", covariant=True)


# NOTE: base type helpers
MethodFuncAny: TypeAlias = t.Callable[..., object]  # type: ignore[explicit-any]
Fallback: TypeAlias = t.Union[type[Exception], t.Sequence[type[Exception]], bool]
Condition: TypeAlias = t.Union[t.Callable[[t.Any], bool], property]  # type: ignore[explicit-any]
ValueGetter: TypeAlias = t.Union[t.Callable[[t.Any], V_co], property]  # type: ignore[explicit-any]


class TransitionBuilder(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __call__(self, func: t.Callable[P, V_co]) -> t.Callable[P, V_co]:
        """Assign transition to provided method function."""
        raise NotImplementedError

    @abc.abstractmethod
    def to(self, destination: State) -> Transition:
        """Set transition destination state."""
        raise NotImplementedError

    @abc.abstractmethod
    def when(self, condition: Condition) -> Transition:
        """Set condition."""
        raise NotImplementedError

    @abc.abstractmethod
    def when_not(self, condition: Condition) -> Transition:
        """Set negative condition."""
        raise NotImplementedError

    @abc.abstractmethod
    def ternary(self, condition: Condition) -> TernaryTransition:
        """Create ternary transition."""
        raise NotImplementedError

    @abc.abstractmethod
    def idempotent(self) -> IdempotentTransition[None]:
        raise NotImplementedError


class StateMachineRegistry:
    def __init__(self, states: t.Sequence[State]) -> None:
        self.__states = list(states)

    @property
    def states(self) -> t.Sequence[State]:
        return self.__states

    @cached_property
    def initial(self) -> State:
        initials = [state for state in self.__states if state.initial]

        if not initials:
            msg = "initial state is not set"
            raise ValueError(msg)

        if len(initials) > 1:
            msg = "initial state ambiguity"
            raise ValueError(msg, initials)

        return next(iter(initials))

    @cached_property
    def finals(self) -> t.Sequence[State]:
        finals = [state for state in self.__states if state.final]

        if not finals:
            msg = "final state is not set"
            raise ValueError(msg)

        return finals

    @cached_property
    def fallbacks(self) -> t.Sequence[State]:
        return [state for state in self.__states if state.fallback]

    @cached_property
    def transitions(self) -> t.Mapping[MethodFuncAny, t.Sequence[Transition]]:
        funcs = defaultdict[MethodFuncAny, list[Transition]](list)

        for state in self.__states:
            for func, transitions in state.transitions:
                funcs[func].extend(transitions)

        return funcs


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

    def register(self, func: MethodFuncAny, transition_def: Transition) -> None:
        if inspect.iscoroutinefunction(func):
            msg = "coroutine functions is not supported"
            # NOTE: inspect returns any
            raise TypeError(msg, func, transition_def)  # type: ignore[misc]

        if func not in self.__funcs:
            self.__funcs[func] = list[Transition]()

        self.__funcs[func].append(transition_def)


class State(TransitionBuilder):
    """Defines state for `DeclarativeStateMachine`"""

    def __init__(
        self,
        name: t.Optional[str] = None,
        *,
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
        return f"<{self.__class__.__name__} at {hex(id(self))}: {self.name}>"

    __repr__ = __str__

    @override
    def __call__(self, func: t.Callable[P, V_co]) -> t.Callable[P, V_co]:
        """Wrap method with cycle transition."""
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

    @override
    def idempotent(self) -> IdempotentTransition[None]:
        return IdempotentTransition(self)


class Transition(TransitionBuilder):
    """
    Defines transition between two states for `DeclarativeStateMachine`.

    You don't have to instantiate this class directly, see `State` methods and example in `DeclarativeStateMachine`.

    Use python decorators to assign transition to some method.
    """

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

    __repr__ = __str__

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
        func = normalize_condition(condition)

        @wraps(func)
        def negate(obj: object) -> bool:
            return not func(obj)

        return self.when(negate)

    @override
    def ternary(self, condition: Condition) -> TernaryTransition:
        return TernaryTransition(self.registry, self.source, condition)

    @override
    def idempotent(self) -> IdempotentTransition[None]:
        if self.destination is None:
            msg = "destination is not set"
            raise RuntimeError(msg, self)

        return IdempotentTransition(self.destination, parents=[self])


class TernaryTransition:
    """
    Helper to build a transition with ternary condition.

    In the following example `transit_ternary` and `transit_s2_or_s3` methods perform transition in the same way:

    >>> class SimpleSM(DeclarativeStateMachine):
    ...     s1, s2, s3 = State(initial=True), State(), State()
    ...
    ...     @property
    ...     def is_ok(self) -> bool:
    ...         raise NotImplementedError
    ...
    ...     @s1.ternary(is_ok).then(s2).otherwise(s3)
    ...     def transit_ternary(self) -> None:
    ...         pass
    ...
    ...     @s1.to(s2).when(is_ok)
    ...     @s1.to(s3).when_not(is_ok)
    ...     def transit_s2_or_s3(self) -> None:
    ...         pass
    """

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
        """Set destination when condition is truthy."""
        self.__then.to(state)
        return self

    def otherwise(self, state: State) -> TernaryTransition:
        """Set destination when condition is falsy."""
        self.__otherwise.to(state)
        return self


class IdempotentTransition(t.Generic[V_co]):
    def __init__(
        self,
        state: State,
        returns: t.Optional[ValueGetter[V_co]] = None,
        parents: t.Optional[t.Sequence[Transition]] = None,
    ) -> None:
        self.__state = state
        self.__returns = returns
        self.__parents = parents

    def __call__(self, func: t.Callable[Concatenate[T, P], None]) -> t.Callable[Concatenate[T, P], V_co]:
        returns = normalize_value_getter(self.__returns) if self.__returns is not None else None

        @wraps(func)
        def wrapper(container: T, /, *args: P.args, **kwargs: P.kwargs) -> V_co:
            if container.current_state is not self.__state:
                func(container, *args, **kwargs)

            result = returns(container) if returns is not None else None

            return result

        for parent in reversed(self.__parents or ()):
            parent(wrapper)

        return self.__state(wrapper)

    def returns(self, returns: ValueGetter[W_co]) -> IdempotentTransition[W_co]:
        return IdempotentTransition(self.__state, returns, self.__parents)


def normalize_value_getter(getter: ValueGetter[V_co]) -> t.Callable[[object], V_co]:
    if isinstance(getter, property):  # type: ignore[misc]
        func: t.Optional[t.Callable[[object], V_co]] = getter.fget

        if func is None:
            msg = "property fget method must be set"
            raise TypeError(msg, getter)

        return func

    return getter


def normalize_condition(condition: Condition) -> t.Callable[[object], bool]:
    # NOTE: we can assume that getter turns truthy value (to be used in `if` statement)
    func = normalize_value_getter(condition)

    @wraps(func)
    def wrapper(obj: object) -> bool:
        return bool(func(obj))

    return wrapper
