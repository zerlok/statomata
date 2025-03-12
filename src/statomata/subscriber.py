import asyncio
import typing as t

from typing_extensions import override

from statomata.abc import StateMachineAsyncSubscriber, StateMachineSubscriber

S_contra = t.TypeVar("S_contra", contravariant=True)
U_contra = t.TypeVar("U_contra", contravariant=True)
V_contra = t.TypeVar("V_contra", contravariant=True)


class StateMachineSubscriberRegistry(
    t.Generic[S_contra, U_contra, V_contra], StateMachineSubscriber[S_contra, U_contra, V_contra]
):
    def __init__(self, *subscribers: StateMachineSubscriber[S_contra, U_contra, V_contra]) -> None:
        self.__subscribers = set(subscribers)

    def register(self, *subscribers: StateMachineSubscriber[S_contra, U_contra, V_contra]) -> None:
        self.__subscribers.update(subscribers)

    def unregister(self, *subscribers: StateMachineSubscriber[S_contra, U_contra, V_contra]) -> None:
        self.__subscribers.difference_update(subscribers)

    @override
    def notify_start(self, state: S_contra) -> None:
        for sub in self.__subscribers:
            sub.notify_start(state)

    @override
    def notify_state_start(self, state: S_contra, income: U_contra) -> None:
        for sub in self.__subscribers:
            sub.notify_state_start(state, income)

    @override
    def notify_state_outcome(self, state: S_contra, income: U_contra, outcome: V_contra) -> None:
        for sub in self.__subscribers:
            sub.notify_state_outcome(state, income, outcome)

    @override
    def notify_state_finish(self, state: S_contra, income: U_contra) -> None:
        for sub in self.__subscribers:
            sub.notify_state_finish(state, income)

    @override
    def notify_state_error(self, state: S_contra, error: Exception) -> None:
        for sub in self.__subscribers:
            sub.notify_state_error(state, error)

    @override
    def notify_transition(self, source: S_contra, dest: S_contra) -> None:
        for sub in self.__subscribers:
            sub.notify_transition(source, dest)

    @override
    def notify_finish(self, state: S_contra) -> None:
        for sub in self.__subscribers:
            sub.notify_finish(state)


class StateMachineAsyncSubscriberRegistry(
    t.Generic[S_contra, U_contra, V_contra],
    StateMachineAsyncSubscriber[S_contra, U_contra, V_contra],
):
    def __init__(self, *subscribers: StateMachineAsyncSubscriber[S_contra, U_contra, V_contra]) -> None:
        self.__subscribers = set(subscribers)

    def register(self, *subscribers: StateMachineAsyncSubscriber[S_contra, U_contra, V_contra]) -> None:
        self.__subscribers.update(subscribers)

    def unregister(self, *subscribers: StateMachineAsyncSubscriber[S_contra, U_contra, V_contra]) -> None:
        self.__subscribers.difference_update(subscribers)

    @override
    async def notify_start(self, state: S_contra) -> None:
        if not self.__subscribers:
            return

        await asyncio.gather(*(sub.notify_start(state) for sub in self.__subscribers))

    @override
    async def notify_state_start(self, state: S_contra, income: U_contra) -> None:
        if not self.__subscribers:
            return

        await asyncio.gather(*(sub.notify_state_start(state, income) for sub in self.__subscribers))

    @override
    async def notify_state_outcome(self, state: S_contra, income: U_contra, outcome: V_contra) -> None:
        if not self.__subscribers:
            return

        await asyncio.gather(*(sub.notify_state_outcome(state, income, outcome) for sub in self.__subscribers))

    @override
    async def notify_state_finish(self, state: S_contra, income: U_contra) -> None:
        if not self.__subscribers:
            return

        await asyncio.gather(*(sub.notify_state_finish(state, income) for sub in self.__subscribers))

    @override
    async def notify_state_error(self, state: S_contra, error: Exception) -> None:
        if not self.__subscribers:
            return

        await asyncio.gather(*(sub.notify_state_error(state, error) for sub in self.__subscribers))

    @override
    async def notify_transition(self, source: S_contra, dest: S_contra) -> None:
        if not self.__subscribers:
            return

        await asyncio.gather(*(sub.notify_transition(source, dest) for sub in self.__subscribers))

    @override
    async def notify_finish(self, state: S_contra) -> None:
        if not self.__subscribers:
            return

        await asyncio.gather(*(sub.notify_finish(state) for sub in self.__subscribers))
