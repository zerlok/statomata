import typing as t
from contextlib import asynccontextmanager, contextmanager

from typing_extensions import override

from statomata.abc import Context, StateMachineAsyncSubscriber, StateMachineSubscriber
from statomata.final import FinalState

# FIXME: find a way to set a bound `State`
S_state = t.TypeVar("S_state")
U_contra = t.TypeVar("U_contra", contravariant=True)
V_contra = t.TypeVar("V_contra", contravariant=True)


class StateMachineExecutor(t.Generic[S_state, U_contra, V_contra], Context[S_state]):
    def __init__(
        self,
        state: S_state,
        fallback: t.Optional[t.Callable[[Exception], t.Optional[S_state]]] = None,
        subscriber: t.Optional[StateMachineSubscriber[S_state, U_contra, V_contra]] = None,
    ) -> None:
        self.__state = state
        self.__next_state: t.Optional[S_state] = None
        self.__fallback = fallback
        self.__subscriber = subscriber

        self.__started = False
        self.__finished = False

    @override
    def set_state(self, state: S_state) -> None:
        self.__next_state = state

    @override
    def set_final_state(self, reason: str, *details: object) -> None:
        # FIXME: possible bug, not sure if final state is a subtype of S_state (see `notify_transitioned`)
        state = t.cast("S_state", FinalState(reason, *details))
        self.set_state(state)

    @property
    def state(self) -> S_state:
        return self.__state

    @property
    def is_started(self) -> bool:
        return self.__started

    @property
    def is_finished(self) -> bool:
        return self.__finished

    @contextmanager
    def visit_state(self, income: U_contra) -> t.Iterator[Context[S_state]]:
        context = self.enter_state(income)
        try:
            yield context

        except Exception as err:
            ok = self.handle_state_error(err)
            if not ok:
                raise

        else:
            self.leave_state(income)

    def enter_state(self, income: U_contra) -> Context[S_state]:
        if not self.__started:
            self.__started = True
            if self.__subscriber is not None:
                self.__subscriber.notify_started(self.__state)

        if self.__subscriber is not None:
            self.__subscriber.notify_state_entered(self.__state, income)

        return self

    def handle_outcome(self, income: U_contra, outcome: V_contra) -> None:
        if self.__subscriber is not None:
            self.__subscriber.notify_state_outcome(self.__state, income, outcome)

    def leave_state(self, income: U_contra) -> None:
        if self.__subscriber is not None:
            self.__subscriber.notify_state_left(self.__state, income)

        self.reset_state()

        if isinstance(self.__state, FinalState):
            self.__finished = True
            if self.__subscriber is not None:
                # FIXME: possible bug, not sure if final state is a subtype of S_state
                self.__subscriber.notify_finished(t.cast("S_state", self.__state))

    def handle_state_error(self, err: Exception) -> bool:
        self.__next_state = None

        if self.__subscriber is not None:
            self.__subscriber.notify_state_failed(self.__state, err)

        if self.__fallback is None:
            return False

        self.__next_state = self.__fallback(err)

        return self.reset_state()

    def reset_state(self) -> bool:
        if self.__next_state is None:
            return False

        source, self.__state, self.__next_state = self.__state, self.__next_state, None

        if self.__subscriber is not None:
            self.__subscriber.notify_transitioned(source, self.__state)

        return True


class AsyncStateMachineExecutor(t.Generic[S_state, U_contra, V_contra], Context[S_state]):
    def __init__(
        self,
        state: S_state,
        fallback: t.Optional[t.Callable[[Exception], t.Optional[S_state]]] = None,
        subscriber: t.Optional[StateMachineAsyncSubscriber[S_state, U_contra, V_contra]] = None,
    ) -> None:
        self.__state = state
        self.__next_state: t.Optional[S_state] = None
        self.__fallback = fallback
        self.__subscriber = subscriber

        self.__started = False
        self.__finished = False

    @override
    def set_state(self, state: S_state) -> None:
        self.__next_state = state

    @override
    def set_final_state(self, reason: str, *details: object) -> None:
        # FIXME: possible bug, not sure if final state is a subtype of S_state (see `notify_transitioned`)
        state = t.cast("S_state", FinalState(reason, *details))
        self.set_state(state)

    @property
    def state(self) -> S_state:
        return self.__state

    @property
    def is_started(self) -> bool:
        return self.__started

    @property
    def is_finished(self) -> bool:
        return self.__finished

    @asynccontextmanager
    async def visit_state(self, income: U_contra) -> t.AsyncIterator[Context[S_state]]:
        context = await self.enter_state(income)
        try:
            yield context

        except Exception as err:
            ok = await self.handle_state_error(err)
            if not ok:
                raise

        else:
            await self.leave_state(income)

    async def enter_state(self, income: U_contra) -> Context[S_state]:
        if not self.__started:
            self.__started = True
            if self.__subscriber is not None:
                await self.__subscriber.notify_started(self.__state)

        if self.__subscriber is not None:
            await self.__subscriber.notify_state_entered(self.__state, income)

        return self

    async def handle_outcome(self, income: U_contra, outcome: V_contra) -> None:
        if self.__subscriber is not None:
            await self.__subscriber.notify_state_outcome(self.__state, income, outcome)

    async def leave_state(self, income: U_contra) -> None:
        if self.__subscriber is not None:
            await self.__subscriber.notify_state_left(self.__state, income)

        await self.reset_state()

        if isinstance(self.__state, FinalState):
            self.__finished = True
            if self.__subscriber is not None:
                # FIXME: possible bug, not sure if final state is a subtype of S_state
                await self.__subscriber.notify_finished(t.cast("S_state", self.__state))

    async def handle_state_error(self, err: Exception) -> bool:
        self.__next_state = None

        if self.__subscriber is not None:
            await self.__subscriber.notify_state_failed(self.__state, err)

        if self.__fallback is None:
            return False

        self.__next_state = self.__fallback(err)

        return await self.reset_state()

    async def reset_state(self) -> bool:
        if self.__next_state is None:
            return False

        source, self.__state, self.__next_state = self.__state, self.__next_state, None

        if self.__subscriber is not None:
            await self.__subscriber.notify_transitioned(source, self.__state)

        return True
