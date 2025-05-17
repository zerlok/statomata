# mypy: disable-error-code="misc, explicit-any"

from __future__ import annotations

import typing as t
from functools import singledispatchmethod, wraps

from typing_extensions import Concatenate, ParamSpec, Self, override

from statomata.abc import StateMachine, StateMachineSubscriber
from statomata.declarative.builder import State, StateMachineRegistry
from statomata.declarative.config import Configurator, Context
from statomata.declarative.state import MethodCall, MethodCallState
from statomata.exception import InvalidStateError

P = ParamSpec("P")
V_co = t.TypeVar("V_co", covariant=True)


class DeclarativeStateMachine(StateMachine[State]):
    """
    Base class to set up state machines in declarative way.

    Derivatives should define states: `State` class attributes (one state must be initial); and methods with state
    transitions.

    Each instance will keep its own state. To perform transitions - invoke appropriate methods with transition
    decorators. Those methods are executed with the following alogirthm:

    1. Acquire the instance lock to prevent other method concurrent execution.
    2. Check if current state matches the transition source. Raise `InvalidStateError` on mismatch.
    3. Enter the state (invokes appropriate subscribers, see `StateMachineExecutor` for more info).
    4. Invoke specified method function (see `MethodCallState` for more info) - provides state `outcome`.
    5. Check transitions to perform transition into new state (see `MethodCallState` for more info).
    6. Notify subscribers about `outcome`.
    7. Leave the state (invokes appropriate subscribers, see `StateMachineExecutor` for more info).
    8. Release lock.
    9. Return `outcome` value.

    Simple state machine defintion example:

    >>> class SimpleSM(DeclarativeStateMachine):
    ...     s1, s2, s3 = State(initial=True), State(), State()
    ...
    ...     def __init__(self, name: str) -> None:
    ...         super().__init__()
    ...         self.__name = name
    ...         self.__cycles = 0
    ...
    ...     @s1 # stay in `s1` state (cycle transition)
    ...     def transit_cycle(self) -> None:
    ...         print("name:", self.__name)
    ...         self.__cycles += 1
    ...
    ...     @s1.to(s2) # transit from `s1` to `s2`
    ...     def transit_from_s1_to_s2(self) -> int:
    ...         return self.__cycles
    ...
    ...     @property
    ...     def can_transit_to_s3(self) -> bool:
    ...         return True
    ...
    ...     @s2.to(s3).when(can_transit_to_s3) # transit from `s2` to `s3` if `can_transit_to_s3`
    ...     def transit_from_s2_to_s3(self, p1: str, p2: str) -> str:
    ...         return ".".join((p1, p2, self.__name))
    """

    __conf: t.ClassVar[Configurator]
    __context: t.ClassVar[Context[Self]]
    __fallback: t.ClassVar[t.Callable[[Self, Exception], t.Optional[MethodCallState[Self]]]]

    @override
    def __init_subclass__(
        cls,
        configurator: t.Optional[Configurator] = None,
        **kwargs: object,
    ) -> None:
        super().__init_subclass__(**kwargs)

        conf = configurator if configurator is not None else Configurator()
        context = conf.context(cls)

        cls.__setup_transitions(conf, context)
        cls.__setup_fallback(conf, context)

        # save all context
        cls.__conf = conf
        cls.__context = t.cast("Context[Self]", context)

    def __init__(
        self,
        initial: t.Optional[State] = None,
        subscribers: t.Optional[
            t.Sequence[StateMachineSubscriber[MethodCallState[Self], MethodCall[Self, object], object]]
        ] = None,
        lock: t.Optional[t.ContextManager[object]] = None,
    ) -> None:
        self.__executor = self.__conf.create_executor(
            self.__context.state(initial if initial is not None else self.__context.registry.initial),
            self.__fallback,
            subscribers,
        )
        self.__lock = lock if lock is not None else self.__conf.create_lock()

    @override
    @property
    def current_state(self) -> State:
        return self.__context.state_def(self.__executor.state)

    @classmethod
    def state_machine_registry(cls) -> StateMachineRegistry:
        return cls.__context.registry

    @classmethod
    def __setup_transitions(cls, conf: Configurator, context: Context[Self]) -> None:
        for func, transition_defs in context.registry.transitions.items():
            sources = {context.state(transition_def.source) for transition_def in transition_defs}

            setattr(cls, func.__name__, cls.__wrap_method(func, sources))

            for transition_def in transition_defs:
                if transition_def.destination is None:
                    msg = "destination is not set"
                    raise ValueError(msg, transition_def)

                source = context.state(transition_def.source)
                destination = context.state(transition_def.destination)

                source.add_transition(conf.build_transition(func, destination, transition_def.condition))

    @classmethod
    def __setup_fallback(cls, conf: Configurator, context: Context[Self]) -> None:
        # NOTE: this is desired behavior
        @singledispatchmethod  # noqa: PLE1520
        def handle(_self: Self, _e: Exception, /) -> t.Optional[MethodCallState[Self]]:
            return None

        for fallback_state_def in context.registry.fallbacks:
            err_types, state_factory = conf.build_fallback(
                fallback=fallback_state_def.fallback,
                state=context.state(fallback_state_def),
            )

            for err_type in err_types:
                handle.register(err_type)(state_factory)

        # FIXME: possible type error
        cls.__fallback = handle  # type: ignore[assignment]

    @classmethod
    def __wrap_method(
        cls,
        func: t.Callable[Concatenate[Self, P], V_co],
        sources: t.Collection[MethodCallState[Self]],
    ) -> t.Callable[Concatenate[Self, P], V_co]:
        @wraps(func)
        def wrapper(self: Self, /, *args: P.args, **kwargs: P.kwargs) -> V_co:
            # prevent concurrent method execution
            with self.__lock:
                executor = self.__executor
                state = executor.state

                # check if current state matches transition source
                if state not in sources:
                    raise InvalidStateError(
                        actual=self.__context.state_def(state),
                        expected={self.__context.state_def(source) for source in sources},
                    )

                income: MethodCall[Self, V_co] = MethodCall(self, func, args, kwargs)

                # execute `MethodCallState`
                with executor.visit_state(income) as context:
                    outcome = state.handle(income, context)
                    executor.handle_outcome(income, outcome)

                    return outcome

        # FIXME: probably a typing error
        return t.cast("t.Callable[Concatenate[Self, P], V_co]", wrapper)
