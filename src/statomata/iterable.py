from __future__ import annotations

import abc
import asyncio
import threading
import typing as t

from typing_extensions import override

from statomata.abc import Context, State, StateMachine

# NOTE: ruff false-positive, `if t.TYPE_CHECKING` causes `NameError: name 'UnaryOptState' is not defined`
from statomata.executor import AsyncStateMachineExecutor, StateMachineExecutor  # noqa: TC001
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


class IterableStateMachine(t.Generic[U_contra, V_co], StateMachine[IterableState[U_contra, V_co]]):
    def __init__(
        self,
        executor: StateMachineExecutor[IterableState[U_contra, V_co], U_contra, V_co],
        lock: t.Optional[t.ContextManager[object]] = None,
    ) -> None:
        self.__executor = executor
        self.__lock = lock if lock is not None else threading.Lock()

    @property
    @override
    def current_state(self) -> IterableState[U_contra, V_co]:
        return self.__executor.current_state

    def run(self, /, incomes: t.Iterable[U_contra]) -> t.Iterable[V_co]:
        with self.__lock:
            for item in incomes:
                for income, context in self.__executor.process(item):
                    for outcome in self.__executor.current_state.handle(income, context):
                        yield outcome
                        self.__executor.handle_outcome(income, outcome)

                if self.__executor.is_aborted:
                    break


class AsyncIterableStateMachine(t.Generic[U_contra, V_co], StateMachine[AsyncIterableState[U_contra, V_co]]):
    def __init__(
        self,
        executor: AsyncStateMachineExecutor[AsyncIterableState[U_contra, V_co], U_contra, V_co],
        lock: t.Optional[t.AsyncContextManager[object]] = None,
    ) -> None:
        self.__executor = executor
        self.__lock = lock if lock is not None else asyncio.Lock()

    @property
    @override
    def current_state(self) -> AsyncIterableState[U_contra, V_co]:
        return self.__executor.current_state

    async def run(self, /, incomes: t.AsyncIterable[U_contra]) -> t.AsyncIterable[V_co]:
        async with self.__lock:
            async for item in incomes:
                async for income, context in self.__executor.process(item):
                    async for outcome in self.__executor.current_state.handle(income, context):
                        yield outcome
                        await self.__executor.handle_outcome(income, outcome)

                if self.__executor.is_aborted:
                    break


class IterableOptStateMachine(t.Generic[U_contra, V_co], StateMachine[UnaryOptState[U_contra, V_co]]):
    def __init__(
        self,
        executor: StateMachineExecutor[UnaryOptState[U_contra, V_co], U_contra, V_co],
        lock: t.Optional[t.ContextManager[object]] = None,
    ) -> None:
        self.__executor = executor
        self.__lock = lock if lock is not None else threading.Lock()

    @property
    @override
    def current_state(self) -> UnaryOptState[U_contra, V_co]:
        return self.__executor.current_state

    def run(self, /, incomes: t.Iterable[U_contra]) -> t.Iterable[V_co]:
        with self.__lock:
            for item in incomes:
                for income, context in self.__executor.process(item):
                    outcome = self.__executor.current_state.handle(income, context)
                    if outcome is not None:
                        yield outcome
                        self.__executor.handle_outcome(income, outcome)

                if self.__executor.is_aborted:
                    break


class AsyncIterableOptStateMachine(t.Generic[U_contra, V_co], StateMachine[AsyncUnaryOptState[U_contra, V_co]]):
    def __init__(
        self,
        executor: AsyncStateMachineExecutor[AsyncUnaryOptState[U_contra, V_co], U_contra, V_co],
        lock: t.Optional[t.AsyncContextManager[object]] = None,
    ) -> None:
        self.__executor = executor
        self.__lock = lock if lock is not None else asyncio.Lock()

    @property
    @override
    def current_state(self) -> AsyncUnaryOptState[U_contra, V_co]:
        return self.__executor.current_state

    async def run(self, /, incomes: t.AsyncIterable[U_contra]) -> t.AsyncIterable[V_co]:
        async with self.__lock:
            async for item in incomes:
                async for income, context in self.__executor.process(item):
                    outcome = await self.__executor.current_state.handle(income, context)
                    if outcome is not None:
                        yield outcome
                        await self.__executor.handle_outcome(income, outcome)

                if self.__executor.is_aborted:
                    break


class IterableSeqStateMachine(t.Generic[U_contra, V_co], StateMachine[UnarySeqState[U_contra, V_co]]):
    def __init__(
        self,
        executor: StateMachineExecutor[UnarySeqState[U_contra, V_co], U_contra, V_co],
        lock: t.Optional[t.ContextManager[object]] = None,
    ) -> None:
        self.__executor = executor
        self.__lock = lock if lock is not None else threading.Lock()

    @property
    @override
    def current_state(self) -> UnarySeqState[U_contra, V_co]:
        return self.__executor.current_state

    def run(self, /, incomes: t.Iterable[U_contra]) -> t.Iterable[V_co]:
        with self.__lock:
            for item in incomes:
                for income, context in self.__executor.process(item):
                    outcomes = self.__executor.current_state.handle(income, context)

                    for outcome in outcomes:
                        yield outcome
                        self.__executor.handle_outcome(income, outcome)

                if self.__executor.is_aborted:
                    break


class AsyncIterableSeqStateMachine(t.Generic[U_contra, V_co], StateMachine[AsyncUnarySeqState[U_contra, V_co]]):
    def __init__(
        self,
        executor: AsyncStateMachineExecutor[AsyncUnarySeqState[U_contra, V_co], U_contra, V_co],
        lock: t.Optional[t.AsyncContextManager[object]] = None,
    ) -> None:
        self.__executor = executor
        self.__lock = lock if lock is not None else asyncio.Lock()

    @property
    @override
    def current_state(self) -> AsyncUnarySeqState[U_contra, V_co]:
        return self.__executor.current_state

    async def run(self, /, incomes: t.AsyncIterable[U_contra]) -> t.AsyncIterable[V_co]:
        async with self.__lock:
            async for item in incomes:
                async for income, context in self.__executor.process(item):
                    outcomes = await self.__executor.current_state.handle(income, context)

                    for outcome in outcomes:
                        yield outcome
                        await self.__executor.handle_outcome(income, outcome)

                if self.__executor.is_aborted:
                    break
