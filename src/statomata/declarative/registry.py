from __future__ import annotations

import typing as t
from functools import cached_property

from statomata.declarative.builder import InvalidOptionsError, MethodFunc, MethodOptions

if t.TYPE_CHECKING:
    from statomata.declarative import State


class StateMachineRegistry:
    def __init__(self, states: t.Mapping[str, State], methods: t.Mapping[MethodFunc, MethodOptions]) -> None:
        self.__states = states
        self.__methods = methods

    @property
    def states(self) -> t.Mapping[str, State]:
        return self.__states

    @cached_property
    def initial(self) -> State:
        initials = [state for state in self.__states.values() if state.initial]

        if not initials:
            msg = "initial state is not set"
            raise InvalidOptionsError(msg, self.__states)

        if len(initials) > 1:
            msg = "initial state ambiguity"
            raise InvalidOptionsError(msg, initials)

        return next(iter(initials))

    @cached_property
    def finals(self) -> t.Sequence[State]:
        finals = [state for state in self.__states.values() if state.final]

        if not finals:
            msg = "final state is not set"
            raise InvalidOptionsError(msg, self.__states)

        return finals

    @cached_property
    def fallbacks(self) -> t.Sequence[State]:
        return [state for state in self.__states.values() if state.fallback]

    @property
    def methods(self) -> t.Mapping[MethodFunc, MethodOptions]:
        return self.__methods
