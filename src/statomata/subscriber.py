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
    def notify_started(self, state: S_contra) -> None:
        for sub in self.__subscribers:
            sub.notify_started(state)

    @override
    def notify_state_entered(self, state: S_contra, income: U_contra) -> None:
        for sub in self.__subscribers:
            sub.notify_state_entered(state, income)

    @override
    def notify_state_outcome(self, state: S_contra, income: U_contra, outcome: V_contra) -> None:
        for sub in self.__subscribers:
            sub.notify_state_outcome(state, income, outcome)

    @override
    def notify_state_left(self, state: S_contra, income: U_contra) -> None:
        for sub in self.__subscribers:
            sub.notify_state_left(state, income)

    @override
    def notify_state_failed(self, state: S_contra, error: Exception) -> None:
        for sub in self.__subscribers:
            sub.notify_state_failed(state, error)

    @override
    def notify_transitioned(self, source: S_contra, dest: S_contra) -> None:
        for sub in self.__subscribers:
            sub.notify_transitioned(source, dest)

    @override
    def notify_finished(self, state: S_contra) -> None:
        for sub in self.__subscribers:
            sub.notify_finished(state)


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
    async def notify_started(self, state: S_contra) -> None:
        if not self.__subscribers:
            return

        await asyncio.gather(*(sub.notify_started(state) for sub in self.__subscribers))

    @override
    async def notify_state_entered(self, state: S_contra, income: U_contra) -> None:
        if not self.__subscribers:
            return

        await asyncio.gather(*(sub.notify_state_entered(state, income) for sub in self.__subscribers))

    @override
    async def notify_state_outcome(self, state: S_contra, income: U_contra, outcome: V_contra) -> None:
        if not self.__subscribers:
            return

        await asyncio.gather(*(sub.notify_state_outcome(state, income, outcome) for sub in self.__subscribers))

    @override
    async def notify_state_left(self, state: S_contra, income: U_contra) -> None:
        if not self.__subscribers:
            return

        await asyncio.gather(*(sub.notify_state_left(state, income) for sub in self.__subscribers))

    @override
    async def notify_state_failed(self, state: S_contra, error: Exception) -> None:
        if not self.__subscribers:
            return

        await asyncio.gather(*(sub.notify_state_failed(state, error) for sub in self.__subscribers))

    @override
    async def notify_transitioned(self, source: S_contra, dest: S_contra) -> None:
        if not self.__subscribers:
            return

        await asyncio.gather(*(sub.notify_transitioned(source, dest) for sub in self.__subscribers))

    @override
    async def notify_finished(self, state: S_contra) -> None:
        if not self.__subscribers:
            return

        await asyncio.gather(*(sub.notify_finished(state) for sub in self.__subscribers))
