from __future__ import annotations

import abc
import asyncio
import threading
import typing as t

from typing_extensions import override

from statomata.abc import Context, State, StateMachine

if t.TYPE_CHECKING:
    from statomata.executor import AsyncStateMachineExecutor, StateMachineExecutor

U_contra = t.TypeVar("U_contra", contravariant=True)
V_co = t.TypeVar("V_co", covariant=True)


class UnaryState(t.Generic[U_contra, V_co], State[U_contra, V_co]):
    """Interface for StateMachine state that handles one income and returns one outcome."""

    @abc.abstractmethod
    @override
    def handle(self, income: U_contra, context: Context[UnaryState[U_contra, V_co]]) -> V_co:
        raise NotImplementedError


class AsyncUnaryState(t.Generic[U_contra, V_co], State[U_contra, t.Awaitable[V_co]]):
    """Interface for asynchronous StateMachine state that handles one income and returns one outcome."""

    @abc.abstractmethod
    @override
    async def handle(self, income: U_contra, context: Context[AsyncUnaryState[U_contra, V_co]]) -> V_co:
        raise NotImplementedError


class UnaryOptState(t.Generic[U_contra, V_co], UnaryState[U_contra, t.Optional[V_co]]):
    """Interface for StateMachine state that handles one income and may return one outcome."""

    @abc.abstractmethod
    @override
    def handle(self, income: U_contra, context: Context[UnaryOptState[U_contra, V_co]]) -> t.Optional[V_co]:
        raise NotImplementedError


class AsyncUnaryOptState(t.Generic[U_contra, V_co], AsyncUnaryState[U_contra, t.Optional[V_co]]):
    """Interface for asynchronous StateMachine state that handles one income and may return one outcome."""

    @abc.abstractmethod
    @override
    async def handle(
        self,
        income: U_contra,
        context: Context[AsyncUnaryOptState[U_contra, V_co]],
    ) -> t.Optional[V_co]:
        raise NotImplementedError


class UnarySeqState(t.Generic[U_contra, V_co], UnaryState[U_contra, t.Sequence[V_co]]):
    """Interface for StateMachine state that handles one income and returns outcome sequence."""

    @abc.abstractmethod
    @override
    def handle(
        self,
        income: U_contra,
        context: Context[UnarySeqState[U_contra, V_co]],
    ) -> t.Sequence[V_co]:
        raise NotImplementedError


class AsyncUnarySeqState(t.Generic[U_contra, V_co], AsyncUnaryState[U_contra, t.Sequence[V_co]]):
    """Interface for asynchronous StateMachine state that handles one income and returns outcome sequence."""

    @abc.abstractmethod
    @override
    async def handle(
        self,
        income: U_contra,
        context: Context[AsyncUnarySeqState[U_contra, V_co]],
    ) -> t.Sequence[V_co]:
        raise NotImplementedError


class UnaryStateMachine(t.Generic[U_contra, V_co], StateMachine[UnaryState[U_contra, V_co]]):
    def __init__(
        self,
        executor: StateMachineExecutor[UnaryState[U_contra, V_co], U_contra, V_co],
        lock: t.Optional[t.ContextManager[object]] = None,
    ) -> None:
        self.__executor = executor
        self.__lock = lock if lock is not None else threading.Lock()

    @property
    @override
    def current_state(self) -> UnaryState[U_contra, V_co]:
        return self.__executor.current_state

    def run(self, /, income: U_contra) -> V_co:
        with self.__lock:
            with self.__executor.visit_state(income) as context:
                outcome = self.current_state.handle(income, context)
                self.__executor.handle_outcome(income, outcome)

            for recalled, context in self.__executor.recall():
                outcome = self.current_state.handle(recalled, context)
                self.__executor.handle_outcome(recalled, outcome)

            return outcome


class AsyncUnaryStateMachine(t.Generic[U_contra, V_co], StateMachine[AsyncUnaryState[U_contra, V_co]]):
    def __init__(
        self,
        executor: AsyncStateMachineExecutor[AsyncUnaryState[U_contra, V_co], U_contra, V_co],
        lock: t.Optional[t.AsyncContextManager[object]] = None,
    ) -> None:
        self.__executor = executor
        self.__lock = lock if lock is not None else asyncio.Lock()

    @property
    @override
    def current_state(self) -> AsyncUnaryState[U_contra, V_co]:
        return self.__executor.current_state

    async def run(self, /, income: U_contra) -> V_co:
        async with self.__lock:
            async with self.__executor.visit_state(income) as context:
                outcome = await self.__executor.current_state.handle(income, context)
                await self.__executor.handle_outcome(income, outcome)

            async for recalled, context in self.__executor.recall():
                outcome = await self.__executor.current_state.handle(recalled, context)
                await self.__executor.handle_outcome(recalled, outcome)

            return outcome
