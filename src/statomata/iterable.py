from __future__ import annotations

import abc
import asyncio
import threading
import typing as t

from typing_extensions import override

from statomata.abc import Context, State, StateMachine

if t.TYPE_CHECKING:
    from statomata.executor import AsyncStateMachineExecutor, StateMachineExecutor
    from statomata.unary import AsyncUnaryOptState, AsyncUnarySeqState, UnaryOptState, UnarySeqState

U_contra = t.TypeVar("U_contra", contravariant=True)
V_co = t.TypeVar("V_co", covariant=True)


class IterableState(t.Generic[U_contra, V_co], State[U_contra, t.Iterable[V_co]]):
    """Interface for StateMachine state that handles one income and generates outcomes."""

    @abc.abstractmethod
    @override
    def handle(self, income: U_contra, context: Context[IterableState[U_contra, V_co]]) -> t.Iterable[V_co]:
        raise NotImplementedError


class AsyncIterableState(t.Generic[U_contra, V_co], State[U_contra, t.AsyncIterable[V_co]]):
    """Interface for asynchronous StateMachine state that handles one income and generates outcomes."""

    @abc.abstractmethod
    @override
    def handle(
        self,
        income: U_contra,
        context: Context[AsyncIterableState[U_contra, V_co]],
    ) -> t.AsyncIterable[V_co]:
        raise NotImplementedError


class IterableStateMachine(t.Generic[U_contra, V_co], StateMachine[t.Iterable[U_contra], t.Iterable[V_co]]):
    def __init__(
        self,
        executor: StateMachineExecutor[IterableState[U_contra, V_co], U_contra, V_co],
    ) -> None:
        self.__executor = executor

        self.__lock = threading.Lock()

    @property
    def current_state(self) -> IterableState[U_contra, V_co]:
        return self.__executor.state

    @override
    def run(self, /, incomes: t.Iterable[U_contra]) -> t.Iterable[V_co]:
        with self.__lock:
            for income in incomes:
                context = self.__executor.start_state(income)

                try:
                    for outcome in self.current_state.handle(income, context):
                        yield outcome
                        self.__executor.handle_outcome(income, outcome)

                except Exception as err:
                    ok = self.__executor.handle_state_error(err)
                    if not ok:
                        raise

                else:
                    self.__executor.finish_state(income)

                if self.__executor.is_finished:
                    return


class AsyncIterableStateMachine(
    t.Generic[U_contra, V_co],
    StateMachine[t.AsyncIterable[U_contra], t.AsyncIterable[V_co]],
):
    def __init__(
        self,
        executor: AsyncStateMachineExecutor[AsyncIterableState[U_contra, V_co], U_contra, V_co],
    ) -> None:
        self.__executor = executor

        self.__lock = asyncio.Lock()

    @property
    def current_state(self) -> AsyncIterableState[U_contra, V_co]:
        return self.__executor.state

    @override
    async def run(self, /, incomes: t.AsyncIterable[U_contra]) -> t.AsyncIterable[V_co]:
        async with self.__lock:
            async for income in incomes:
                context = await self.__executor.start_state(income)

                try:
                    async for outcome in self.current_state.handle(income, context):
                        yield outcome
                        await self.__executor.handle_outcome(income, outcome)

                except Exception as err:
                    ok = await self.__executor.handle_state_error(err)
                    if not ok:
                        raise

                else:
                    await self.__executor.finish_state(income)

                if self.__executor.is_finished:
                    return


class IterableOptStateMachine(t.Generic[U_contra, V_co], StateMachine[t.Iterable[U_contra], t.Iterable[V_co]]):
    def __init__(
        self,
        executor: StateMachineExecutor[UnaryOptState[U_contra, V_co], U_contra, V_co],
    ) -> None:
        self.__executor = executor

        self.__lock = threading.Lock()

    @property
    def current_state(self) -> UnaryOptState[U_contra, V_co]:
        return self.__executor.state

    @override
    def run(self, /, incomes: t.Iterable[U_contra]) -> t.Iterable[V_co]:
        with self.__lock:
            for income in incomes:
                context = self.__executor.start_state(income)

                try:
                    outcome = self.current_state.handle(income, context)

                except Exception as err:
                    ok = self.__executor.handle_state_error(err)
                    if not ok:
                        raise

                else:
                    if outcome is not None:
                        yield outcome
                        self.__executor.handle_outcome(income, outcome)

                    self.__executor.finish_state(income)

                if self.__executor.is_finished:
                    return


class AsyncIterableOptStateMachine(
    t.Generic[U_contra, V_co],
    StateMachine[t.AsyncIterable[U_contra], t.AsyncIterable[V_co]],
):
    def __init__(
        self,
        executor: AsyncStateMachineExecutor[AsyncUnaryOptState[U_contra, V_co], U_contra, V_co],
    ) -> None:
        self.__executor = executor

        self.__lock = asyncio.Lock()

    @property
    def current_state(self) -> AsyncUnaryOptState[U_contra, V_co]:
        return self.__executor.state

    @override
    async def run(self, /, incomes: t.AsyncIterable[U_contra]) -> t.AsyncIterable[V_co]:
        async with self.__lock:
            async for income in incomes:
                context = await self.__executor.start_state(income)

                try:
                    outcome = await self.current_state.handle(income, context)

                except Exception as err:
                    ok = await self.__executor.handle_state_error(err)
                    if not ok:
                        raise

                else:
                    if outcome is not None:
                        yield outcome
                        await self.__executor.handle_outcome(income, outcome)

                    await self.__executor.finish_state(income)

                if self.__executor.is_finished:
                    return


class IterableSeqStateMachine(t.Generic[U_contra, V_co], StateMachine[t.Iterable[U_contra], t.Iterable[V_co]]):
    def __init__(
        self,
        executor: StateMachineExecutor[UnarySeqState[U_contra, V_co], U_contra, V_co],
    ) -> None:
        self.__executor = executor

        self.__lock = threading.Lock()

    @property
    def current_state(self) -> UnarySeqState[U_contra, V_co]:
        return self.__executor.state

    @override
    def run(self, /, incomes: t.Iterable[U_contra]) -> t.Iterable[V_co]:
        with self.__lock:
            for income in incomes:
                context = self.__executor.start_state(income)

                try:
                    outcomes = self.current_state.handle(income, context)

                except Exception as err:
                    ok = self.__executor.handle_state_error(err)
                    if not ok:
                        raise

                else:
                    for outcome in outcomes:
                        yield outcome
                        self.__executor.handle_outcome(income, outcome)

                    self.__executor.finish_state(income)

                if self.__executor.is_finished:
                    return


class AsyncIterableSeqStateMachine(
    t.Generic[U_contra, V_co],
    StateMachine[t.AsyncIterable[U_contra], t.AsyncIterable[V_co]],
):
    def __init__(
        self,
        executor: AsyncStateMachineExecutor[AsyncUnarySeqState[U_contra, V_co], U_contra, V_co],
    ) -> None:
        self.__executor = executor

        self.__lock = asyncio.Lock()

    @property
    def current_state(self) -> AsyncUnarySeqState[U_contra, V_co]:
        return self.__executor.state

    @override
    async def run(self, /, incomes: t.AsyncIterable[U_contra]) -> t.AsyncIterable[V_co]:
        async with self.__lock:
            async for income in incomes:
                context = await self.__executor.start_state(income)

                try:
                    outcomes = await self.current_state.handle(income, context)

                except Exception as err:
                    ok = await self.__executor.handle_state_error(err)
                    if not ok:
                        raise

                else:
                    for outcome in outcomes:
                        yield outcome
                        await self.__executor.handle_outcome(income, outcome)

                    await self.__executor.finish_state(income)

                if self.__executor.is_finished:
                    return
