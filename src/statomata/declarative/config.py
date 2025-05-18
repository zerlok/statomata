# mypy: disable-error-code="misc, explicit-any"

from __future__ import annotations

import inspect
import threading
import typing as t

from typing_extensions import ParamSpec, assert_never

from statomata.abc import StateMachine
from statomata.declarative.builder import (
    ConditionalTransitionOptions,
    ConstantTransitionOptions,
    Fallback,
    KeyMappingTransitionOptions,
    MethodFunc,
    MethodOptions,
    NullTransitionOptions,
    State,
    TransitionOptions,
    get_method_options,
)
from statomata.declarative.registry import StateMachineRegistry
from statomata.declarative.state import (
    ConditionalMethodCallTransition,
    ConstantMethodCallTransition,
    KeyMappingMethodCallTransition,
    MethodCall,
    MethodCallState,
    MethodCallTransition,
)
from statomata.executor import StateMachineExecutor
from statomata.subscriber.registry import StateMachineSubscriberRegistry

if t.TYPE_CHECKING:
    from statomata.abc import StateMachineSubscriber

P = ParamSpec("P")
V_co = t.TypeVar("V_co", covariant=True)
S_sm = t.TypeVar("S_sm", bound=StateMachine[State])


class Configurator:
    def context(self, sm_class: type[S_sm]) -> Context[S_sm]:
        registry = self.registry(sm_class)
        return Context(
            registry=registry,
            state_map={
                state: self.build_state(
                    sm_class=sm_class,
                    name=state.name or name,
                    initial=state.initial,
                    final=state.final,
                )
                for name, state in registry.states.items()
            },
        )

    def registry(self, sm_class: type[S_sm]) -> StateMachineRegistry:
        states = dict[str, State]()
        methods = dict[MethodFunc, MethodOptions]()

        name: str
        obj: object

        for name, obj in inspect.getmembers(sm_class):  # type: ignore[misc]
            if isinstance(obj, State):
                state_name = obj.name = obj.name or name
                states[state_name] = obj
                obj.freeze()

            elif callable(obj):
                options = get_method_options(obj)
                if options is not None:
                    methods[obj] = options

        return StateMachineRegistry(states, methods)

    def create_lock(self) -> t.ContextManager[object]:
        return threading.Lock()

    def create_executor(
        self,
        initial: MethodCallState[S_sm],
        fallback: t.Optional[t.Callable[[Exception], t.Optional[MethodCallState[S_sm]]]] = None,
        subscribers: t.Optional[
            t.Sequence[StateMachineSubscriber[MethodCallState[S_sm], MethodCall[S_sm, object], object]]
        ] = None,
    ) -> StateMachineExecutor[MethodCallState[S_sm], MethodCall[S_sm, object], object]:
        return StateMachineExecutor(
            state=initial,
            fallback=fallback,
            subscriber=StateMachineSubscriberRegistry(*subscribers) if subscribers else None,
        )

    # NOTE: only python 3.12 supports generic methods
    def build_state(self, *, sm_class: type[S_sm], name: str, initial: bool, final: bool) -> MethodCallState[S_sm]:  # noqa: ARG002
        return MethodCallState[S_sm](name=name, initial=initial, final=final)

    def build_transition(
        self,
        options: TransitionOptions,
        context: Context[S_sm],
    ) -> t.Optional[MethodCallTransition[S_sm]]:
        if isinstance(options, NullTransitionOptions):
            return None

        elif isinstance(options, ConstantTransitionOptions):
            return ConstantMethodCallTransition(context.state(options.destination))

        elif isinstance(options, ConditionalTransitionOptions):
            return ConditionalMethodCallTransition(options.predicate, context.state(options.destination))

        elif isinstance(options, KeyMappingTransitionOptions):
            return KeyMappingMethodCallTransition(
                key=options.key,
                destinations={key: context.state(dest) for key, dest in options.destinations.items()},
                default=context.state(options.default) if options.default is not None else None,
            )

        else:
            assert_never(options)

    def build_fallback(
        self,
        fallback: Fallback,
        state: MethodCallState[S_sm],
    ) -> tuple[t.Sequence[type[Exception]], t.Callable[[S_sm, Exception], t.Optional[MethodCallState[S_sm]]]]:
        def factory(_s: S_sm, _e: Exception, /) -> t.Optional[MethodCallState[S_sm]]:
            return state

        if isinstance(fallback, bool):
            return ((Exception,), factory) if fallback else ((), factory)

        elif isinstance(fallback, type) and issubclass(fallback, Exception):
            return (fallback,), factory

        elif isinstance(fallback, t.Sequence):
            return tuple(fallback), factory

        else:
            assert_never(fallback)


class Context(t.Generic[S_sm]):
    def __init__(
        self,
        registry: StateMachineRegistry,
        state_map: t.Mapping[State, MethodCallState[S_sm]],
    ) -> None:
        self.__registry = registry
        self.__state_map = state_map
        self.__state_def_map = {state: state_def for state_def, state in state_map.items()}

    @property
    def registry(self) -> StateMachineRegistry:
        return self.__registry

    def state(self, state_def: State) -> MethodCallState[S_sm]:
        return self.__state_map[state_def]

    def state_def(self, state_def: MethodCallState[S_sm]) -> State:
        return self.__state_def_map[state_def]
