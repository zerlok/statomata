import typing as t

from typing_extensions import override

from statomata.abc import StateMachineAsyncSubscriber, StateMachineSubscriber

S_contra = t.TypeVar("S_contra", contravariant=True)
U_contra = t.TypeVar("U_contra", contravariant=True)
V_contra = t.TypeVar("V_contra", contravariant=True)


class SubscriberStub(StateMachineSubscriber[S_contra, U_contra, V_contra]):
    def __init__(self) -> None:
        self.__events = list[tuple[S_contra, str]]()
        self.__transition = list[tuple[S_contra, S_contra]]()

    @override
    def notify_initial(self, state: S_contra) -> None:
        self.__events.append((state, "initial"))

    @override
    def notify_state_entered(self, state: S_contra, income: U_contra) -> None:
        self.__events.append((state, "state_entered"))

    @override
    def notify_state_outcome(self, state: S_contra, income: U_contra, outcome: V_contra) -> None:
        self.__events.append((state, "state_outcome"))

    @override
    def notify_state_left(self, state: S_contra, income: U_contra) -> None:
        self.__events.append((state, "state_left"))

    @override
    def notify_state_failed(self, state: S_contra, error: Exception) -> None:
        self.__events.append((state, "state_failed"))

    @override
    def notify_transition(self, source: S_contra, destination: S_contra) -> None:
        self.__events.append((source, "transition"))
        self.__transition.append((source, destination))

    @override
    def notify_final(self, state: S_contra) -> None:
        self.__events.append((state, "final"))

    @property
    def events(self) -> t.Sequence[tuple[S_contra, str]]:
        return self.__events

    @property
    def transitions(self) -> t.Sequence[tuple[S_contra, S_contra]]:
        return self.__transition


class SubscriberAsyncStub(StateMachineAsyncSubscriber[S_contra, U_contra, V_contra]):
    def __init__(self) -> None:
        self.__events = list[tuple[S_contra, str]]()
        self.__transition = list[tuple[S_contra, S_contra]]()

    @override
    async def notify_initial(self, state: S_contra) -> None:
        self.__events.append((state, "initial"))

    @override
    async def notify_state_entered(self, state: S_contra, income: U_contra) -> None:
        self.__events.append((state, "state_entered"))

    @override
    async def notify_state_outcome(self, state: S_contra, income: U_contra, outcome: V_contra) -> None:
        self.__events.append((state, "state_outcome"))

    @override
    async def notify_state_left(self, state: S_contra, income: U_contra) -> None:
        self.__events.append((state, "state_left"))

    @override
    async def notify_state_failed(self, state: S_contra, error: Exception) -> None:
        self.__events.append((state, "state_failed"))

    @override
    async def notify_transition(self, source: S_contra, destination: S_contra) -> None:
        self.__events.append((source, "transition"))
        self.__transition.append((source, destination))

    @override
    async def notify_final(self, state: S_contra) -> None:
        self.__events.append((state, "final"))

    @property
    def events(self) -> t.Sequence[tuple[S_contra, str]]:
        return self.__events

    @property
    def transitions(self) -> t.Sequence[tuple[S_contra, S_contra]]:
        return self.__transition
