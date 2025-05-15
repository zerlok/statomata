# mypy: disable-error-code="misc, explicit-any"

from __future__ import annotations

import inspect
import typing as t

from typing_extensions import Concatenate, ParamSpec, assert_never

from statomata.declarative.builder import Condition, Fallback, State, StateRegistry
from statomata.declarative.state import MethodCallState, MethodCallTransition

P = ParamSpec("P")
T = t.TypeVar("T")
V_co = t.TypeVar("V_co", covariant=True)


class Configurator:
    def context(self, klass: type[T]) -> Context[T]:
        registry = self.registry(klass)
        return Context(
            registry=registry,
            state_map={state_def: MethodCallState[T](state_def.name) for state_def in registry.states},
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

    def build_transition(
        self,
        func: t.Callable[Concatenate[T, P], V_co],
        destination: MethodCallState[T],
        condition: t.Optional[Condition] = None,
    ) -> MethodCallTransition[T]:
        if isinstance(condition, property) and condition.fget is None:
            msg = "property fget method must be set"
            raise TypeError(msg, condition)

        return MethodCallTransition(
            func=func,
            condition=condition.fget
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
    ) -> tuple[t.Sequence[type[Exception]], t.Callable[[Exception], t.Optional[MethodCallState[T]]]]:
        def factory(_: Exception) -> t.Optional[MethodCallState[T]]:
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
