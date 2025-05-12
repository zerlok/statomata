import typing as t

from typing_extensions import override

from statomata.abc import Context, FinalStateAlreadyReachedError, State

U_contra = t.TypeVar("U_contra", contravariant=True)
V_co = t.TypeVar("V_co", covariant=True)


class FinalState(t.Generic[U_contra, V_co], State[U_contra, V_co]):
    def __init__(self, reason: str, *details: object) -> None:
        self.__reason = reason
        self.__details = details

    @property
    def reason(self) -> str:
        return self.__reason

    @property
    def details(self) -> t.Sequence[object]:
        return self.__details

    @t.final
    @override
    def handle(self, event: U_contra, context: Context[State[U_contra, V_co]]) -> V_co:
        raise FinalStateAlreadyReachedError(self.__reason, *self.__details, event, context)
