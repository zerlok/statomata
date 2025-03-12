import typing as t

from typing_extensions import override

from statomata.abc import Context, State, StateMachineFinalStateReachedError


class FinalState(State[object, object]):
    def __init__(self, reason: str, *details: object) -> None:
        self.__reason = reason
        self.__details = details

    @t.final
    @override
    def handle(self, event: object, context: Context[State[object, object]]) -> t.NoReturn:
        raise StateMachineFinalStateReachedError(self.__reason, *self.__details, event, context)
