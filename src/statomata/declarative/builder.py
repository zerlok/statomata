from __future__ import annotations

import typing as t
from collections import defaultdict
from dataclasses import dataclass, field
from functools import wraps

from typing_extensions import ParamSpec, TypeAlias, override

from statomata.abc import StateMachineError
from statomata.transition import ConditionalTransition, ConstantTransition, MappingTransition, Transition

P = ParamSpec("P")
T = t.TypeVar("T")
V_co = t.TypeVar("V_co", covariant=True)
W_co = t.TypeVar("W_co", covariant=True)


# NOTE: base type helpers
MethodTransition: TypeAlias = Transition[object, object]
MethodFunc: TypeAlias = t.Callable[..., object]  # type: ignore[explicit-any]
Fallback: TypeAlias = t.Union[type[Exception], t.Sequence[type[Exception]], bool]
Condition: TypeAlias = t.Union[t.Callable[[t.Any], bool], property]  # type: ignore[explicit-any]
ValueGetter: TypeAlias = t.Union[t.Callable[[t.Any], V_co], property]  # type: ignore[explicit-any]


class DeclarativeStateMachineError(StateMachineError):
    pass


class BuildError(DeclarativeStateMachineError):
    pass


class InvalidOptionsError(BuildError):
    pass


class State:
    """
    Defines state for `DeclarativeStateMachine`.

    - name -- a custom name for a state
    - initial -- instantiate state machine with this state
    - final -- abort state machine after transitioning into this state
    - fallback -- specify exceptions to handle during state machine executions
    """

    def __init__(
        self,
        *,
        name: t.Optional[str] = None,
        initial: bool = False,
        final: bool = False,
        fallback: Fallback = False,
    ) -> None:
        self.__name = name
        self.__initial = initial
        self.__final = final
        self.__fallback = fallback
        self.__frozen = False

    @override
    def __str__(self) -> str:
        return f"<{self.__class__.__name__} at {hex(id(self))}: {self.__name}>"

    __repr__ = __str__

    def __call__(self, func: t.Callable[P, V_co]) -> t.Callable[P, V_co]:
        """Assign provided method with null transition."""
        self.__check_not_frozen()
        update_method_options(func, self)
        return func

    @property
    def name(self) -> t.Optional[str]:
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        self.__check_not_frozen()
        self.__name = value

    @property
    def initial(self) -> bool:
        return self.__initial

    @property
    def final(self) -> bool:
        return self.__final

    @property
    def fallback(self) -> Fallback:
        return self.__fallback

    def to(self, destination: State) -> TransitionBuilder:
        """Create transition to specified destination."""
        self.__check_not_frozen()
        return TransitionBuilder(self, destination)

    def cycle(self) -> TransitionBuilder:
        """Create cycle transition."""
        self.__check_not_frozen()
        return self.to(self)

    def ternary(self, condition: Condition) -> TernaryTransitionBuilder:
        """Create ternary transition."""
        self.__check_not_frozen()
        return TernaryTransitionBuilder(self, condition)

    def idempotent(self) -> IdempotentTransitionBuilder[None]:
        """
        Build idempotent transition for a method.

        The wrapped method invocation will be ignored when state machine is in `source` state.
        See `DeclarativeStateMachine` for mode details.
        """
        self.__check_not_frozen()
        return IdempotentTransitionBuilder(self)

    def freeze(self) -> None:
        """Freeze the state, denying any modifications."""
        self.__frozen = True

    def __check_not_frozen(self) -> None:
        if self.__frozen:
            msg = "can't modify frozen state"
            raise BuildError(msg, self)


class TransitionBuilder:
    """
    Defines transition between two states for `DeclarativeStateMachine`.

    By default, the transition is constant - the state machine will perform the transition from source to destination.

    If condition is specified - the state machine will check the transition and if true - perform the transition.

    You don't have to instantiate this class directly, see `State` methods and example in `DeclarativeStateMachine`.

    Use python decorators to assign transition to some method.
    """

    def __init__(
        self,
        source: State,
        destination: State,
    ) -> None:
        if source.final:
            msg = "can't use final state as transition source"
            raise InvalidOptionsError(msg, source)

        self.__source = source
        self.__destination = destination
        self.__condition: t.Optional[Condition] = None

    @override
    def __str__(self) -> str:
        return f"<{self.__class__.__name__}: {self.__source} -> {self.__destination}>"

    __repr__ = __str__

    def __call__(self, func: t.Callable[P, V_co]) -> t.Callable[P, V_co]:
        """Assign transition to provided method function."""
        update_method_options(func, self.__source, self.__build())
        return func

    def when(self, condition: Condition) -> TransitionBuilder:
        """Set condition."""
        self.__condition = condition
        return self

    def when_not(self, condition: Condition) -> TransitionBuilder:
        """Set negative condition."""
        func = normalize_condition(condition)

        @wraps(func)
        def negate(obj: object) -> bool:
            return not func(obj)

        return self.when(negate)

    def ternary(self, condition: Condition) -> TernaryTransitionBuilder:
        """Create ternary transition."""
        return TernaryTransitionBuilder(self.__source, condition, self.__destination)

    def __build(self) -> t.Sequence[MethodTransition]:
        if self.__condition is not None:
            return [ConditionalTransition(normalize_condition(self.__condition), self.__destination)]

        return [ConstantTransition(self.__destination)]


class TernaryTransitionBuilder:
    """
    Builder for ternary condition.

    If condition is true - transit to `then` state, otherwise - transit to `otherwise` state if it is specified.

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
        source: State,
        condition: Condition,
        then: t.Optional[State] = None,
        otherwise: t.Optional[State] = None,
    ) -> None:
        self.__source = source
        self.__condition = condition
        self.__then = then
        self.__otherwise = otherwise

    def __call__(self, func: t.Callable[P, V_co]) -> t.Callable[P, V_co]:
        update_method_options(func, self.__source, self.__build())
        return func

    def then(self, state: State) -> TernaryTransitionBuilder:
        """Set destination when condition is true."""
        self.__then = state
        return self

    def otherwise(self, state: State) -> TernaryTransitionBuilder:
        """Set destination when condition is false."""
        self.__otherwise = state
        return self

    def __build(self) -> t.Sequence[MethodTransition]:
        if self.__then is None:
            return []

        if self.__otherwise is None:
            return [ConditionalTransition(normalize_condition(self.__condition), self.__then)]

        return [MappingTransition(normalize_condition(self.__condition), {True: self.__then, False: self.__otherwise})]


class IdempotentTransitionBuilder(t.Generic[V_co]):
    """
    Build the idempotent transition.

    If state machine is in source state - the wrapped method won't be executed.

    If `returns` is specified - it will be executed in either way and its value will be returned as `outcome`.
    """

    def __init__(
        self,
        source: State,
        returns: t.Optional[ValueGetter[V_co]] = None,
    ) -> None:
        self.__source = source
        self.__returns = returns

    def __call__(self, func: t.Callable[P, None]) -> t.Callable[P, V_co]:
        update_method_options(
            func=func,
            idempotent=IdempotentOptions(
                state=self.__source,
                returns=normalize_value_getter(self.__returns) if self.__returns is not None else None,
            ),
        )

        # NOTE: method will be replaced in `DeclarativeStateMachine`
        return t.cast("t.Callable[P, V_co]", func)

    def returns(self, returns: ValueGetter[W_co]) -> IdempotentTransitionBuilder[W_co]:
        return IdempotentTransitionBuilder(self.__source, returns)


@dataclass()
class IdempotentOptions:
    state: State
    returns: t.Optional[t.Callable[[object], object]] = None


def _create_transitions() -> dict[State, list[MethodTransition]]:
    return defaultdict[State, list[MethodTransition]](list)


@dataclass()
class MethodOptions:
    transitions: dict[State, list[MethodTransition]] = field(default_factory=_create_transitions)
    idempotent: t.Optional[IdempotentOptions] = None


__METHOD_OPTIONS_ATTR: t.Final[str] = "__statomata_method_options__"


def get_method_options(func: t.Callable[P, V_co]) -> t.Optional[MethodOptions]:
    options: object = getattr(func, __METHOD_OPTIONS_ATTR, None)
    return options if isinstance(options, MethodOptions) else None


def update_method_options(
    func: t.Callable[P, V_co],
    source: t.Optional[State] = None,
    transitions: t.Optional[t.Sequence[MethodTransition]] = None,
    idempotent: t.Optional[IdempotentOptions] = None,
) -> None:
    options = get_method_options(func)

    if options is None:
        options = MethodOptions()
        setattr(func, __METHOD_OPTIONS_ATTR, options)

    if source is not None:
        options.transitions[source].extend(transitions or ())

    if idempotent is not None:
        options.idempotent = idempotent


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
    return normalize_value_getter(condition)
