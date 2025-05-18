# mypy: disable-error-code="misc, explicit-any"

from __future__ import annotations

import typing as t
from functools import singledispatchmethod, wraps

from typing_extensions import Concatenate, ParamSpec, Self, override

from statomata.abc import StateMachine, StateMachineSubscriber
from statomata.declarative.builder import MethodOptions, State
from statomata.declarative.config import Configurator, Context
from statomata.declarative.state import MethodCall, MethodCallState
from statomata.exception import InvalidStateError

if t.TYPE_CHECKING:
    from statomata.declarative.registry import StateMachineRegistry


P = ParamSpec("P")
V_co = t.TypeVar("V_co", covariant=True)


class DeclarativeStateMachine(StateMachine[State]):
    """
    Base class to set up state machines in declarative way.

    Derivatives should define states: `State` class attributes; and methods with state transitions.

    Instances of this class are isolated (each instance keeps and manages its own state). You can use `self` parameter
    in transition methods and to access custom properties and methods.

    States properties:

    - only one state should be initial -- the state machine will start from this state by default.
    - some states may be final -- the state machine will abort execution after transition is made into final state.
    - fallback states will allow to catch appropriate exceptions, the state machine will transition into appropriate
      fallback state.

    To perform transitions - invoke appropriate methods with transition decorators. Those methods are executed using the
    following alogirthm:

    1. Acquire the instance lock to prevent other method concurrent execution.
    2. Check if current state matches the transition source. Raise `InvalidStateError` on mismatch.
    3. Enter the state (invokes appropriate subscribers, see `StateMachineExecutor` for more info).
    4. Invoke specified method function (see `MethodCallState` for more info) - provides state `outcome`. If method has
       idempotent state and state machine is in that state -- this step is skipped, but if `returns` is set - its value
       will be returned as outcome in either way.
    5. Check transitions to perform transition into new state (see `MethodCallState` for more info).
    6. Notify subscribers about `outcome`.
    7. Leave the state (invokes appropriate subscribers, see `StateMachineExecutor` for more info).
    8. Release lock.
    9. Return `outcome` value.

    Simple state machine defintion example:

    >>> class SimpleSMExample(DeclarativeStateMachine):
    ...     s1, s2, s3 = State(initial=True), State(), State()
    ...
    ...     def __init__(self, name: str, *, allow_s3: bool = False) -> None:
    ...         super().__init__()
    ...         self.__name = name
    ...         self.__cycles = 0
    ...         self.__allow_s3 = allow_s3
    ...
    ...     @property
    ...     def cycles(self) -> int:
    ...         return self.__cycles
    ...
    ...     @property
    ...     def can_transit_to_s3(self) -> bool:
    ...         return True
    ...
    ...     @s1 # stay in `s1` state (cycle transition)
    ...     def transit_cycle(self) -> None:
    ...         print("name:", self.__name)
    ...         self.__cycles += 1
    ...
    ...     @s1.to(s2) # transit from `s1` to `s2`
    ...     @s2.idempotent().returns(cycles)
    ...     def transit_from_s1_to_s2(self) -> None:
    ...         pass
    ...
    ...     @s2.to(s3).when(can_transit_to_s3) # transit from `s2` to `s3` if `can_transit_to_s3`
    ...     def transit_from_s2_to_s3(self, p1: str, p2: str) -> str:
    ...         return ".".join((p1, p2, self.__name))
    """

    __configurator: t.ClassVar[Configurator]
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
        cls.__configurator = conf
        cls.__context = t.cast("Context[Self]", context)

    def __init__(
        self,
        initial: t.Optional[State] = None,
        subscribers: t.Optional[
            t.Sequence[StateMachineSubscriber[MethodCallState[Self], MethodCall[Self, object], object]]
        ] = None,
        lock: t.Optional[t.ContextManager[object]] = None,
    ) -> None:
        self.__executor = self.__configurator.create_executor(
            initial=self.__context.state(initial if initial is not None else self.__context.registry.initial),
            fallback=self.__fallback,
            subscribers=subscribers,
        )
        self.__lock = lock if lock is not None else self.__configurator.create_lock()

    @override
    @property
    def current_state(self) -> State:
        return self.__context.state_def(self.__executor.state)

    @classmethod
    def state_machine_registry(cls) -> StateMachineRegistry:
        return cls.__context.registry

    @classmethod
    def __setup_transitions(cls, conf: Configurator, context: Context[Self]) -> None:
        for fn, options in context.registry.methods.items():
            func = cls.__normalize_method(fn, options, context)

            setattr(cls, func.__name__, cls.__wrap_method(func, options, context))

            for opt in options.transitions:
                transition = conf.build_transition(opt, context)
                if transition is not None:
                    source = context.state(opt.source)
                    source.add_transitions(func, transition)

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

        # NOTE: singledispatchmethod signature is not compatible with Callable
        cls.__fallback = t.cast("t.Callable[[Self, Exception], t.Optional[MethodCallState[Self]]]", handle)

    @classmethod
    def __normalize_method(
        cls,
        func: t.Callable[Concatenate[Self, P], V_co],
        options: MethodOptions,
        context: Context[Self],
    ) -> t.Callable[Concatenate[Self, P], V_co]:
        if options.idempotent is None:
            return func

        idempotent_state = context.state(options.idempotent.state)

        # NOTE: returns is used to return `V_co` value, see `IdempotentTransitionBuilder`
        returns = t.cast(
            "t.Callable[[Self], V_co]",
            options.idempotent.returns if options.idempotent.returns is not None else cls.__none,
        )

        @wraps(func)
        def wrapper(self: Self, /, *args: P.args, **kwargs: P.kwargs) -> V_co:
            if self.__executor.state is not idempotent_state:
                func(self, *args, **kwargs)

            return returns(self)

        return wrapper

    @classmethod
    def __none(cls, _: Self, /) -> None:
        return None

    @classmethod
    def __wrap_method(
        cls,
        func: t.Callable[Concatenate[Self, P], V_co],
        options: MethodOptions,
        context: Context[Self],
    ) -> t.Callable[Concatenate[Self, P], V_co]:
        sources = {context.state(transition.source) for transition in options.transitions}

        @wraps(func)
        def wrapper(self: Self, /, *args: P.args, **kwargs: P.kwargs) -> V_co:
            # prevent concurrent method execution
            with self.__lock:
                executor = self.__executor
                current_state = executor.state

                # check if current state matches transition source
                if current_state not in sources:
                    raise InvalidStateError(
                        actual=self.__context.state_def(current_state),
                        expected={self.__context.state_def(source) for source in sources},
                    )

                income: MethodCall[Self, V_co] = MethodCall(self, func, args, kwargs)

                # execute `MethodCallState`
                with executor.visit_state(income) as ctx:
                    outcome = current_state.handle(income, ctx)
                    executor.handle_outcome(income, outcome)

                    return outcome

        # FIXME: probably a typing error
        return t.cast("t.Callable[Concatenate[Self, P], V_co]", wrapper)
