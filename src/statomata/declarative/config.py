# mypy: disable-error-code="misc, explicit-any"

from __future__ import annotations

import inspect
import threading
import typing as t

from typing_extensions import Concatenate, ParamSpec, assert_never

from statomata.declarative.builder import Condition, Fallback, State, StateRegistry, extract_property_getter
from statomata.declarative.state import MethodCall, MethodCallState, MethodCallTransition
from statomata.executor import StateMachineExecutor
from statomata.subscriber.registry import StateMachineSubscriberRegistry

if t.TYPE_CHECKING:
    from statomata.abc import StateMachineSubscriber

P = ParamSpec("P")
T = t.TypeVar("T")
V_co = t.TypeVar("V_co", covariant=True)


class Configurator:
    def context(self, klass: type[T]) -> Context[T]:
        registry = self.registry(klass)
        return Context(
            registry=registry,
            state_map={state_def: self.build_state(klass, state_def) for state_def in registry.states},
        )

    def registry(self, klass: type[T]) -> StateRegistry:
        state_defs = list[State]()

        name: str
        obj: object

        for name, obj in inspect.getmembers(klass):  # type: ignore[misc]
            if isinstance(obj, State):
                if not obj.name:
                    obj.name = name

                state_defs.append(obj)

        return StateRegistry(state_defs)

    def create_lock(self) -> t.ContextManager[object]:
        return threading.Lock()

    def create_sm_executor(
        self,
        initial: MethodCallState[T],
        fallback: t.Optional[t.Callable[[Exception], t.Optional[MethodCallState[T]]]] = None,
        subscribers: t.Optional[
            t.Sequence[StateMachineSubscriber[MethodCallState[T], MethodCall[T, object], object]]
        ] = None,
    ) -> StateMachineExecutor[MethodCallState[T], MethodCall[T, object], object]:
        return StateMachineExecutor(
            initial,
            fallback,
            StateMachineSubscriberRegistry(*subscribers) if subscribers else None,
        )

    # NOTE: only python 3.12 supports generic methods
    def build_state(self, klass: type[T], state_def: State) -> MethodCallState[T]:  # noqa: ARG002
        return MethodCallState[T](state_def.name)

    def build_transition(
        self,
        func: t.Callable[Concatenate[T, P], V_co],
        destination: MethodCallState[T],
        condition: t.Optional[Condition] = None,
    ) -> MethodCallTransition[T]:
        return MethodCallTransition(
            func=func,
            condition=extract_property_getter(condition)
            if isinstance(condition, property)
            else condition
            if condition is not None
            else truthy,
            destination=destination,
        )

    def build_fallback(
        self,
        fallback: Fallback,
        state: MethodCallState[T],
    ) -> tuple[t.Sequence[type[Exception]], t.Callable[[T, Exception], t.Optional[MethodCallState[T]]]]:
        def factory(_s: T, _e: Exception) -> t.Optional[MethodCallState[T]]:
            return state

        if isinstance(fallback, bool):
            return ((Exception,), factory) if fallback else ((), factory)

        elif isinstance(fallback, type) and issubclass(fallback, Exception):
            return (fallback,), factory

        elif isinstance(fallback, t.Sequence):
            return tuple(fallback), factory

        else:
            assert_never(fallback)


class Context(t.Generic[T]):
    def __init__(
        self,
        registry: StateRegistry,
        state_map: t.Mapping[State, MethodCallState[T]],
    ) -> None:
        self.__registry = registry
        self.__state_map = state_map
        self.__state_def_map = {state: state_def for state_def, state in state_map.items()}

    @property
    def registry(self) -> StateRegistry:
        return self.__registry

    def state(self, state_def: State) -> MethodCallState[T]:
        return self.__state_map[state_def]

    def state_def(self, state_def: MethodCallState[T]) -> State:
        return self.__state_def_map[state_def]


def truthy(_: object) -> bool:
    return True
