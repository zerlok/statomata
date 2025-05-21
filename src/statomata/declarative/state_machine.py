# mypy: disable-error-code="misc, explicit-any"

from __future__ import annotations

import inspect
import typing as t
from contextlib import contextmanager
from functools import singledispatchmethod, wraps

from typing_extensions import Concatenate, ParamSpec, Self, override

from statomata.abc import Context, StateMachine, StateMachineSubscriber
from statomata.declarative.builder import MethodFunc, MethodOptions, State
from statomata.declarative.config import Configurator
from statomata.exception import InvalidStateError
from statomata.executor import StateMachineExecutor
from statomata.transition import TransitionExecutor

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
    4. Invoke specified method function, the return value is considered as state `outcome`.
       If method has idempotent state and state machine is in that state -- this step is skipped, returned outcome is
       always the result of `returns` function if specified, otherwise `None`.
    5. Yield `outcome` if method is generator function or async generator function.
    6. Notify subscribers about `outcome`. For generators invoked on each outcome.
    7. Check transitions to perform transition into new state (see `TransitionExecutor` for more info).
    8. Leave the state (invokes appropriate subscribers, see `StateMachineExecutor` for more info).
    9. Release lock.
    10. Return `outcome` value (if not generator function or async generator function).

    Simple state machine defintion example:

    >>> class SimpleSMExample(DeclarativeStateMachine):
    ...     s1, s2, s3 = State(initial=True), State(), State()
    ...
    ...     def __init__(self, name: str, *, allow_s3: bool = False) -> None:
    ...         super().__init__()
    ...         self.__name = name
    ...         self.__cntr = 0
    ...         self.__allow_s3 = allow_s3
    ...
    ...     @property
    ...     def counter(self) -> int:
    ...         return self.__cntr
    ...
    ...     @property
    ...     def can_transit_to_s3(self) -> bool:
    ...         return self.__allow_s3
    ...
    ...     @s1 # mark the following method to be executed only in `s1` state
    ...     def transit_cycle(self) -> None:
    ...         print("name:", self.__name)
    ...         self.__cntr += 1
    ...
    ...     @s1.to(s2) # transit from `s1` to `s2`
    ...     @s2.idempotent().returns(counter) # mark `s2` as idempotent state, return `counter` value always
    ...     def transit_from_s1_to_s2(self) -> None:
    ...         print("s1 -> s2")
    ...
    ...     @s2.to(s3).when(can_transit_to_s3) # transit from `s2` to `s3` if `can_transit_to_s3`
    ...     def transit_from_s2_to_s3(self, p1: str, p2: str) -> str:
    ...         return ".".join((p1, p2, self.__name))
    """

    __configurator: t.ClassVar[Configurator]
    __registry: t.ClassVar[StateMachineRegistry]
    __transitions: t.ClassVar[TransitionExecutor[tuple[MethodFunc, State], StateMachine[State], State]]
    __fallback: t.ClassVar[t.Callable[[StateMachine[State], Exception], t.Optional[State]]]

    @override
    def __init_subclass__(
        cls,
        configurator: t.Optional[Configurator] = None,
        **kwargs: object,
    ) -> None:
        super().__init_subclass__(**kwargs)

        conf = configurator if configurator is not None else Configurator()
        registry = conf.registry(cls)

        cls.__transitions = conf.create_transition_executor(cls)

        cls.__setup_fallback(conf, registry)
        cls.__setup_methods(conf, registry)

        # save all context
        cls.__configurator = conf
        cls.__registry = registry

    def __init__(
        self,
        initial: t.Optional[State] = None,
        subscribers: t.Optional[t.Sequence[StateMachineSubscriber[State, Self, object]]] = None,
        lock: t.Optional[t.ContextManager[object]] = None,
    ) -> None:
        self.__executor = self.__configurator.create_state_executor(
            initial=initial if initial is not None else self.__registry.initial,
            fallback=self.__fallback,
            subscribers=subscribers,
            is_async=self.__registry.is_async,
        )
        self.__lock = lock if lock is not None else self.__configurator.create_lock()

    @override
    @property
    def current_state(self) -> State:
        return self.__executor.state

    @classmethod
    def state_machine_registry(cls) -> StateMachineRegistry:
        return cls.__registry

    @classmethod
    def __setup_methods(cls, conf: Configurator, registry: StateMachineRegistry) -> None:
        for method, options in registry.methods.items():
            func = cls.__normalize_method(method, options)

            for source, transitions in options.transitions.items():
                cls.__transitions.add_transitions((func, source), *transitions)

            setattr(cls, func.__name__, cls.__wrap_method(func, options))

    @classmethod
    def __setup_fallback(cls, conf: Configurator, registry: StateMachineRegistry) -> None:
        # NOTE: this is desired behavior
        @singledispatchmethod  # noqa: PLE1520
        def handle(_self: object, _e: Exception, /) -> t.Optional[State]:
            return None

        for state in registry.fallbacks:
            err_types, state_factory = conf.build_fallback(state)

            for err_type in err_types:
                handle.register(err_type)(state_factory)

        # NOTE: singledispatchmethod signature is not compatible with Callable
        cls.__fallback = t.cast("t.Callable[[object, Exception], t.Optional[State]]", handle)

    @classmethod
    def __wrap_method(
        cls,
        func: t.Callable[Concatenate[Self, P], V_co],
        options: MethodOptions,
    ) -> t.Callable[Concatenate[Self, P], V_co]:
        sources = set(options.transitions.keys())
        if options.idempotent:
            sources.add(options.idempotent.state)

        # if inspect.isasyncgenfunction(func):
        #
        #     @wraps(func)
        #     async def wrapper(self: Self, /, *args: P.args, **kwargs: P.kwargs) -> t.AsyncIterable[V_co]:
        #         async with self.__provide_async_executor(sources) as (executor, context):
        #             async for outcome in func(self, *args, **kwargs):
        #                 yield outcome
        #                 await executor.handle_outcome(self, outcome)
        #
        #             self.__transitions.execute((func, self.current_state), self, context)
        #
        # elif inspect.iscoroutinefunction(func):
        #
        #     @wraps(func)
        #     async def wrapper(self: Self, /, *args: P.args, **kwargs: P.kwargs) -> V_co:
        #         async with self.__provide_async_executor(sources) as (executor, context):
        #             outcome = await func(self, *args, **kwargs)
        #             await executor.handle_outcome(self, outcome)
        #
        #             self.__transitions.execute((func, self.current_state), self, context)
        #
        #             return outcome

        if inspect.isgeneratorfunction(func):
            iterfunc: t.Callable[Concatenate[Self, P], t.Iterable[V_co]] = func

            @wraps(func)
            def wrapper(self: Self, /, *args: P.args, **kwargs: P.kwargs) -> t.Iterable[V_co]:
                with self.__provide_executor(func, sources) as (executor, context):
                    for outcome in iterfunc(self, *args, **kwargs):
                        yield outcome
                        executor.handle_outcome(self, outcome)

                    self.__transitions.execute((func, self.current_state), self, context)

        else:

            @wraps(func)
            def wrapper(self: Self, /, *args: P.args, **kwargs: P.kwargs) -> V_co:
                with self.__provide_executor(func, sources) as (executor, context):
                    outcome = func(self, *args, **kwargs)
                    executor.handle_outcome(self, outcome)

                    self.__transitions.execute((func, self.current_state), self, context)

                    return outcome

        # FIXME: probably a typing error
        return t.cast("t.Callable[Concatenate[Self, P], V_co]", wrapper)

    @classmethod
    def __normalize_method(
        cls,
        func: t.Callable[Concatenate[Self, P], V_co],
        options: MethodOptions,
    ) -> t.Callable[Concatenate[Self, P], V_co]:
        if options.idempotent is None:
            return func

        idempotent_state = options.idempotent.state

        # if inspect.iscoroutinefunction(func):
        #     # NOTE: returns is used to return `V_co` value, see `IdempotentTransitionBuilder`
        #     returns_async = t.cast(
        #         "t.Callable[[Self], t.Awaitable[V_co]]",
        #         options.idempotent.returns if options.idempotent.returns is not None else cls.__none_async,
        #     )
        #
        #     @wraps(func)
        #     async def wrapper(self: Self, /, *args: P.args, **kwargs: P.kwargs) -> V_co:
        #         if self.current_state is not idempotent_state:
        #             await func(self, *args, **kwargs)
        #
        #         return await returns_async(self)
        # else:

        # NOTE: returns is used to return `V_co` value, see `IdempotentTransitionBuilder`
        returns = t.cast(
            "t.Callable[[Self], V_co]",
            options.idempotent.returns if options.idempotent.returns is not None else cls.__none,
        )

        @wraps(func)
        def wrapper(self: Self, /, *args: P.args, **kwargs: P.kwargs) -> V_co:
            if self.current_state is not idempotent_state:
                func(self, *args, **kwargs)

            return returns(self)

        return wrapper

    @classmethod
    def __none(cls, _: Self, /) -> None:
        return None

    @classmethod
    async def __none_async(cls, _: Self, /) -> None:
        return None

    @contextmanager
    def __provide_executor(
        self,
        func: t.Callable[P, V_co],
        sources: t.Collection[State],
    ) -> t.Iterator[tuple[StateMachineExecutor[State, Self, V_co], Context[State]]]:
        # prevent concurrent method execution
        with self.__lock:
            current_state = self.current_state

            # check if current state matches transition source
            if current_state not in sources:
                raise InvalidStateError(actual=current_state, expected=sources)

            assert isinstance(self.__executor, StateMachineExecutor)

            with self.__executor.visit_state(self) as context:
                yield self.__executor, context

    # @asynccontextmanager
    # async def __provide_async_executor(
    #     self,
    #     sources: t.Collection[State],
    # ) -> t.AsyncIterator[tuple[AsyncStateMachineExecutor[State, Self, V_co]], Context[State]]:
    #     # prevent concurrent method execution
    #     async with self.__lock:
    #         current_state = self.current_state
    #
    #         # check if current state matches transition source
    #         if current_state not in sources:
    #             raise InvalidStateError(actual=current_state, expected=sources)
    #
    #         executor: AsyncStateMachineExecutor[State, Self, V_co] = self.__executor
    #         async with executor.visit_state(self) as context:
    #             yield executor, context
