# mypy: disable-error-code="misc, explicit-any"

from __future__ import annotations

import threading
import typing as t
from functools import singledispatch, wraps

from typing_extensions import Concatenate, ParamSpec, Self, override

from statomata.abc import InvalidStateError, StateMachine
from statomata.declarative.builder import State
from statomata.declarative.config import Configurator, Context
from statomata.declarative.state import MethodCall, MethodCallState
from statomata.executor import StateMachineExecutor

P = ParamSpec("P")
V_co = t.TypeVar("V_co", covariant=True)


class DeclarativeStateMachine(StateMachine[State]):
    __context: t.ClassVar[Context[Self]]
    __fallback_handler: t.ClassVar[t.Callable[[Exception], t.Optional[MethodCallState[Self]]]]

    @override
    def __init_subclass__(
        cls,
        configurator: t.Optional[Configurator] = None,
        **kwargs: object,
    ) -> None:
        conf = configurator if configurator is not None else Configurator()
        context = conf.context(cls)

        for source_def in context.registry.states:
            for func, transition_defs in source_def.transitions:
                source = context.state(source_def)

                setattr(cls, func.__name__, cls.__wrap_method(func, source))

                for transition_def in transition_defs:
                    if transition_def.destination is None:
                        msg = "destination is not set"
                        raise ValueError(msg, transition_def)

                    destination = context.state(transition_def.destination)
                    source.add_transition(conf.build_transition(func, destination, transition_def.condition))

        @singledispatch
        def handle(_: Exception) -> t.Optional[MethodCallState[Self]]:
            return None

        for fallback_state_def in context.registry.fallbacks:
            err_types, state_factory = conf.build_fallback(
                fallback=fallback_state_def.fallback,
                state=context.state(fallback_state_def),
            )

            for err_type in err_types:
                # FIXME: check if typing error
                handle.register(err_type)(state_factory)  # type: ignore[arg-type]

        cls.__fallback_handler = handle

        cls.__context = t.cast("Context[Self]", context)

    def __init__(
        self,
        initial: t.Optional[State] = None,
        lock: t.Optional[threading.Lock] = None,
    ) -> None:
        self.__lock = lock if lock is not None else threading.Lock()
        self.__executor = StateMachineExecutor[MethodCallState[Self], MethodCall[Self, object], object](
            state=self.__context.state(initial if initial is not None else self.__context.registry.initial),
            # FIXME: check if typing error
            fallback=self.__fallback_handler,  # type: ignore[arg-type]
        )

    @override
    @property
    def current_state(self) -> State:
        return self.__context.state_def(self.__executor.state)

    @classmethod
    def __wrap_method(
        cls,
        func: t.Callable[Concatenate[Self, P], V_co],
        expected_state: MethodCallState[Self],
    ) -> t.Callable[Concatenate[Self, P], V_co]:
        @wraps(func)
        def wrapper(self: Self, *args: P.args, **kwargs: P.kwargs) -> V_co:
            with self.__lock:
                executor = self.__executor
                state = executor.state

                if state is not expected_state:
                    raise InvalidStateError(state, expected_state)

                income: MethodCall[Self, V_co] = MethodCall(self, func, args, kwargs)

                with executor.visit_state(income) as context:
                    outcome = state.handle(income, context)
                    executor.handle_outcome(income, outcome)

                    return outcome

        # FIXME: probably a typing error
        return t.cast("t.Callable[Concatenate[Self, P], V_co]", wrapper)
