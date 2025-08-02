# mypy: disable-error-code="misc, explicit-any"

from __future__ import annotations

import asyncio
import inspect
import threading
import typing as t

from typing_extensions import ParamSpec, assert_never

from statomata.abc import AsyncStateMachineSubscriber, StateMachine
from statomata.declarative.builder import MethodFunc, MethodOptions, State, get_method_options
from statomata.declarative.registry import StateMachineRegistry
from statomata.executor import AsyncStateMachineExecutor, StateMachineExecutor
from statomata.subscriber.registry import AsyncStateMachineSubscriberRegistry, StateMachineSubscriberRegistry
from statomata.transition import (
    AsyncTransitionExecutor,
    TransitionExecutor,
)

if t.TYPE_CHECKING:
    from statomata.abc import StateMachineSubscriber

P = ParamSpec("P")
V_co = t.TypeVar("V_co", covariant=True)
S_sm = t.TypeVar("S_sm", bound=StateMachine[State])


class BaseConfigurator:
    def registry(self, sm_class: type[S_sm]) -> StateMachineRegistry:
        states = dict[str, State]()
        methods = dict[MethodFunc, MethodOptions]()

        name: str
        obj: object

        for name, obj in inspect.getmembers(sm_class):
            if isinstance(obj, State):
                state_name = obj.name = obj.name or name
                states[state_name] = obj
                obj.freeze()

            elif callable(obj):
                options = get_method_options(obj)
                if options is not None:
                    methods[obj] = options

        return StateMachineRegistry(states, methods)

    def build_fallback(
        self,
        state: State,
    ) -> tuple[t.Sequence[type[Exception]], t.Callable[[S_sm, Exception], t.Optional[State]]]:
        def factory(_s: S_sm, _e: Exception, /) -> t.Optional[State]:
            return state

        if isinstance(state.fallback, bool):
            return ((Exception,), factory) if state.fallback else ((), factory)

        elif isinstance(state.fallback, type) and issubclass(state.fallback, Exception):
            return (state.fallback,), factory

        elif isinstance(state.fallback, t.Sequence):
            return tuple(state.fallback), factory

        else:
            assert_never(state.fallback)


class Configurator(BaseConfigurator):
    def create_lock(self) -> t.ContextManager[object]:
        return threading.Lock()

    def create_state_executor(
        self,
        initial: State,
        fallback: t.Optional[t.Callable[[Exception], t.Optional[State]]] = None,
        subscribers: t.Optional[t.Sequence[StateMachineSubscriber[State, S_sm, object]]] = None,
    ) -> StateMachineExecutor[State, S_sm, object]:
        return StateMachineExecutor(
            state=initial,
            fallback=fallback,
            subscriber=StateMachineSubscriberRegistry(*subscribers) if subscribers else None,
        )

    def create_transition_executor(
        self,
        # NOTE: python 3.9 doesn't support generic method syntax
        sm_class: type[S_sm],  # noqa: ARG002
    ) -> TransitionExecutor[tuple[MethodFunc, State], S_sm, State]:
        return TransitionExecutor()


class AsyncConfigurator(BaseConfigurator):
    def create_lock(self) -> t.AsyncContextManager[object]:
        return asyncio.Lock()

    def create_state_executor(
        self,
        initial: State,
        fallback: t.Optional[t.Callable[[Exception], t.Optional[State]]] = None,
        subscribers: t.Optional[t.Sequence[AsyncStateMachineSubscriber[State, S_sm, object]]] = None,
    ) -> AsyncStateMachineExecutor[State, S_sm, object]:
        return AsyncStateMachineExecutor(
            state=initial,
            fallback=fallback,
            subscriber=AsyncStateMachineSubscriberRegistry(*subscribers) if subscribers else None,
        )

    def create_transition_executor(
        self,
        # NOTE: python 3.9 doesn't support generic method syntax
        sm_class: type[S_sm],  # noqa: ARG002
    ) -> AsyncTransitionExecutor[tuple[MethodFunc, State], S_sm, State]:
        return AsyncTransitionExecutor()
