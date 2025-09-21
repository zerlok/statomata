import asyncio
import typing as t

from typing_extensions import override

from statomata.abc import AsyncStateMachineSubscriber, StateMachineSubscriber

S_contra = t.TypeVar("S_contra", contravariant=True)
U_contra = t.TypeVar("U_contra", contravariant=True)
V_contra = t.TypeVar("V_contra", contravariant=True)


class StateMachineSubscriberRegistry(
    t.Generic[S_contra, U_contra, V_contra],
    StateMachineSubscriber[S_contra, U_contra, V_contra],
):
    def __init__(self, *subscribers: StateMachineSubscriber[S_contra, U_contra, V_contra]) -> None:
        self.__subscribers = set(subscribers)

    def register(self, *subscribers: StateMachineSubscriber[S_contra, U_contra, V_contra]) -> None:
        self.__subscribers.update(subscribers)

    def unregister(self, *subscribers: StateMachineSubscriber[S_contra, U_contra, V_contra]) -> None:
        self.__subscribers.difference_update(subscribers)

    @override
    def notify_initial(self, state: S_contra) -> None:
        for sub in self.__subscribers:
            sub.notify_initial(state)

    @override
    def notify_state_entered(self, state: S_contra, income: U_contra) -> None:
        for sub in self.__subscribers:
            sub.notify_state_entered(state, income)

    @override
    def notify_income_deferred(self, state: S_contra, income: U_contra) -> None:
        for sub in self.__subscribers:
            sub.notify_income_deferred(state, income)

    @override
    def notify_income_recalled(self, state: S_contra, income: U_contra) -> None:
        for sub in self.__subscribers:
            sub.notify_income_recalled(state, income)

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
    def notify_transition(self, source: S_contra, destination: S_contra) -> None:
        for sub in self.__subscribers:
            sub.notify_transition(source, destination)

    @override
    def notify_final(self, state: S_contra) -> None:
        for sub in self.__subscribers:
            sub.notify_final(state)


class AsyncStateMachineSubscriberRegistry(
    t.Generic[S_contra, U_contra, V_contra],
    AsyncStateMachineSubscriber[S_contra, U_contra, V_contra],
):
    def __init__(self, *subscribers: AsyncStateMachineSubscriber[S_contra, U_contra, V_contra]) -> None:
        self.__subscribers = set(subscribers)

    def register(self, *subscribers: AsyncStateMachineSubscriber[S_contra, U_contra, V_contra]) -> None:
        self.__subscribers.update(subscribers)

    def unregister(self, *subscribers: AsyncStateMachineSubscriber[S_contra, U_contra, V_contra]) -> None:
        self.__subscribers.difference_update(subscribers)

    @override
    async def notify_initial(self, state: S_contra) -> None:
        if not self.__subscribers:
            return

        await asyncio.gather(*(sub.notify_initial(state) for sub in self.__subscribers))

    @override
    async def notify_state_entered(self, state: S_contra, income: U_contra) -> None:
        if not self.__subscribers:
            return

        await asyncio.gather(*(sub.notify_state_entered(state, income) for sub in self.__subscribers))

    @override
    async def notify_income_deferred(self, state: S_contra, income: U_contra) -> None:
        if not self.__subscribers:
            return

        await asyncio.gather(*(sub.notify_income_deferred(state, income) for sub in self.__subscribers))

    @override
    async def notify_income_recalled(self, state: S_contra, income: U_contra) -> None:
        if not self.__subscribers:
            return

        await asyncio.gather(*(sub.notify_income_recalled(state, income) for sub in self.__subscribers))

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
    async def notify_transition(self, source: S_contra, destination: S_contra) -> None:
        if not self.__subscribers:
            return

        await asyncio.gather(*(sub.notify_transition(source, destination) for sub in self.__subscribers))

    @override
    async def notify_final(self, state: S_contra) -> None:
        if not self.__subscribers:
            return

        await asyncio.gather(*(sub.notify_final(state) for sub in self.__subscribers))
