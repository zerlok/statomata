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


class UnaryStateMachine(StateMachine[U_contra, V_co]):
    def __init__(
        self,
        executor: StateMachineExecutor[UnaryState[U_contra, V_co], U_contra, V_co],
    ) -> None:
        self.__executor = executor

        self.__lock = threading.Lock()

    @property
    def current_state(self) -> UnaryState[U_contra, V_co]:
        return self.__executor.state

    @override
    def run(self, /, income: U_contra) -> V_co:
        with self.__lock:
            context = self.__executor.start_state(income)
            try:
                outcome = self.current_state.handle(income, context)

            except Exception as err:
                self.__executor.handle_state_error(err)
                raise

            else:
                self.__executor.handle_outcome(income, outcome)
                self.__executor.finish_state(income)

            return outcome


class AsyncUnaryStateMachine(StateMachine[U_contra, t.Awaitable[V_co]]):
    def __init__(
        self,
        executor: AsyncStateMachineExecutor[AsyncUnaryState[U_contra, V_co], U_contra, V_co],
    ) -> None:
        self.__executor = executor

        self.__lock = asyncio.Lock()

    @property
    def current_state(self) -> AsyncUnaryState[U_contra, V_co]:
        return self.__executor.state

    @override
    async def run(self, /, income: U_contra) -> V_co:
        async with self.__lock:
            context = await self.__executor.start_state(income)
            try:
                outcome = await self.current_state.handle(income, context)

            except Exception as err:
                await self.__executor.handle_state_error(err)
                raise

            else:
                await self.__executor.handle_outcome(income, outcome)
                await self.__executor.finish_state(income)

                return outcome
