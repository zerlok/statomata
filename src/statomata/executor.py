import typing as t
from collections import deque
from contextlib import asynccontextmanager, contextmanager

from typing_extensions import override

from statomata.abc import AsyncStateMachineSubscriber, Context, StateMachine, StateMachineSubscriber
from statomata.exception import AbortedStateReachedError

# FIXME: find a way to set a bound `State`
S_state = t.TypeVar("S_state")
U_contra = t.TypeVar("U_contra", contravariant=True)
V_contra = t.TypeVar("V_contra", contravariant=True)
V_co = t.TypeVar("V_co", covariant=True)


class ExecutorContext(t.Generic[S_state, U_contra, V_co], Context[S_state]):
    def __init__(self, state: S_state) -> None:
        self.source = state
        self.destination: t.Optional[S_state] = None

        self.initial = True
        self.entered = False
        self.deferred = False
        self.recalled = False
        self.aborted = False

    @override
    def set_state(self, state: S_state, *, final: bool = False) -> None:
        self.destination = state
        self.recalled = False
        self.aborted = final

    @override
    def defer(self) -> None:
        self.deferred = True

    @override
    def recall(self) -> None:
        self.recalled = True

    @override
    def abort(self) -> None:
        self.aborted = True

    @property
    def can_transit(self) -> bool:
        return self.destination is not None and self.source is not self.destination

    def transit(self) -> tuple[S_state, t.Optional[S_state]]:
        if self.destination is None:
            return self.source, None

        source, self.source, self.destination, self.entered = self.source, self.destination, None, False

        return source, self.source


class StateMachineExecutor(t.Generic[S_state, U_contra, V_contra], StateMachine[S_state]):
    def __init__(
        self,
        state: S_state,
        fallback: t.Optional[t.Callable[[Exception], t.Optional[S_state]]] = None,
        subscriber: t.Optional[StateMachineSubscriber[S_state, U_contra, V_contra]] = None,
        pending: t.Optional[t.MutableSequence[U_contra]] = None,
    ) -> None:
        self.__context = ExecutorContext[S_state, U_contra, V_contra](state)
        self.__fallback = fallback
        self.__subscriber = subscriber
        self.__pending = pending if pending is not None else deque[U_contra]()

    @override
    @property
    def current_state(self) -> S_state:
        return self.__context.source

    @property
    def is_aborted(self) -> bool:
        return self.__context.aborted

    def process(self, income: U_contra) -> t.Iterable[tuple[U_contra, Context[S_state]]]:
        if not self.is_aborted:
            with self.visit_state(income) as context:
                yield income, context

        yield from self.recall()

    def recall(self) -> t.Iterable[tuple[U_contra, Context[S_state]]]:
        while not self.is_aborted and self.__context.recalled and self.__pending:
            income = self.__pending.pop()
            if self.__subscriber is not None:
                self.__subscriber.notify_income_recalled(self.current_state, income)

            self.__context.recalled = False

            with self.visit_state(income) as context:
                yield income, context

    @contextmanager
    def visit_state(self, income: U_contra) -> t.Iterator[Context[S_state]]:
        context = self.enter_state(income)
        try:
            yield context

        except Exception as err:
            self.handle_state_error(err)
            raise

        else:
            self.leave_state(income)

    def enter_state(self, income: U_contra) -> Context[S_state]:
        if self.is_aborted:
            raise AbortedStateReachedError(self.current_state, income)

        if self.__context.initial:
            if self.__subscriber is not None:
                self.__subscriber.notify_initial(self.current_state)

            self.__context.initial = False

        if not self.__context.entered:
            if self.__subscriber is not None:
                self.__subscriber.notify_state_entered(self.current_state, income)

            self.__context.entered = True

        return self.__context

    def handle_outcome(self, income: U_contra, outcome: V_contra) -> None:
        if self.__subscriber is not None:
            self.__subscriber.notify_state_outcome(self.current_state, income, outcome)

    def leave_state(self, income: U_contra) -> None:
        if self.__context.deferred:
            self.__pending.append(income)
            if self.__subscriber is not None:
                self.__subscriber.notify_income_deferred(self.current_state, income)

            self.__context.deferred = False

        if self.__context.can_transit and self.__subscriber is not None:
            self.__subscriber.notify_state_left(self.current_state, income)

        self.reset_state()

        if self.is_aborted and self.__subscriber is not None:
            self.__subscriber.notify_final(self.current_state)

    def handle_state_error(self, err: Exception) -> bool:
        if self.__subscriber is not None:
            self.__subscriber.notify_state_failed(self.current_state, err)

        if self.__fallback is None:
            return False

        fallback = self.__fallback(err)
        if fallback is None:
            return False

        self.__context.set_state(fallback)
        return self.reset_state()

    def reset_state(self) -> bool:
        if not self.__context.can_transit:
            return False

        source, destination = self.__context.transit()
        if destination is not None and self.__subscriber is not None:
            self.__subscriber.notify_transition(source, destination)

        return destination is not None


class AsyncStateMachineExecutor(t.Generic[S_state, U_contra, V_contra], StateMachine[S_state]):
    def __init__(
        self,
        state: S_state,
        fallback: t.Optional[t.Callable[[Exception], t.Optional[S_state]]] = None,
        subscriber: t.Optional[AsyncStateMachineSubscriber[S_state, U_contra, V_contra]] = None,
        pending: t.Optional[t.MutableSequence[U_contra]] = None,
    ) -> None:
        self.__context = ExecutorContext[S_state, U_contra, V_contra](state)
        self.__fallback = fallback
        self.__subscriber = subscriber
        self.__pending = pending if pending is not None else deque[U_contra]()

    @override
    @property
    def current_state(self) -> S_state:
        return self.__context.source

    @property
    def is_aborted(self) -> bool:
        return self.__context.aborted

    async def process(self, income: U_contra) -> t.AsyncIterable[tuple[U_contra, Context[S_state]]]:
        if not self.is_aborted:
            async with self.visit_state(income) as context:
                yield income, context

        async for recalled, context in self.recall():
            yield recalled, context

    async def recall(self) -> t.AsyncIterable[tuple[U_contra, Context[S_state]]]:
        while not self.is_aborted and self.__context.recalled and self.__pending:
            income = self.__pending.pop()
            if self.__subscriber is not None:
                await self.__subscriber.notify_income_recalled(self.current_state, income)

            self.__context.recalled = False

            async with self.visit_state(income) as context:
                yield income, context

    @asynccontextmanager
    async def visit_state(self, income: U_contra) -> t.AsyncIterator[Context[S_state]]:
        context = await self.enter_state(income)
        try:
            yield context

        except Exception as err:
            await self.handle_state_error(err)
            raise

        else:
            await self.leave_state(income)

    async def enter_state(self, income: U_contra) -> Context[S_state]:
        if self.is_aborted:
            raise AbortedStateReachedError(self.current_state, income)

        if self.__context.initial:
            if self.__subscriber is not None:
                await self.__subscriber.notify_initial(self.__context.source)

            self.__context.initial = False

        if not self.__context.entered:
            if self.__subscriber is not None:
                await self.__subscriber.notify_state_entered(self.__context.source, income)

            self.__context.entered = True

        return self.__context

    async def handle_outcome(self, income: U_contra, outcome: V_contra) -> None:
        if self.__subscriber is not None:
            await self.__subscriber.notify_state_outcome(self.__context.source, income, outcome)

    async def leave_state(self, income: U_contra) -> None:
        if self.__context.deferred:
            self.__pending.append(income)
            if self.__subscriber is not None:
                await self.__subscriber.notify_income_deferred(self.current_state, income)

            self.__context.deferred = False

        if self.__context.can_transit and self.__subscriber is not None:
            await self.__subscriber.notify_state_left(self.current_state, income)

        await self.reset_state()

        if self.is_aborted and self.__subscriber is not None:
            await self.__subscriber.notify_final(self.current_state)

    async def handle_state_error(self, err: Exception) -> bool:
        if self.__subscriber is not None:
            await self.__subscriber.notify_state_failed(self.current_state, err)

        if self.__fallback is None:
            return False

        fallback = self.__fallback(err)
        if fallback is None:
            return False

        self.__context.set_state(fallback)
        return await self.reset_state()

    async def reset_state(self) -> bool:
        if not self.__context.can_transit:
            return False

        source, destination = self.__context.transit()
        if destination is not None and self.__subscriber is not None:
            await self.__subscriber.notify_transition(source, destination)

        return destination is not None
