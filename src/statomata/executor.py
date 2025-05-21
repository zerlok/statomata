import typing as t
from contextlib import asynccontextmanager, contextmanager

from typing_extensions import override

from statomata.abc import AsyncStateMachineSubscriber, Context, StateMachineSubscriber
from statomata.exception import AbortedStateReachedError

# FIXME: find a way to set a bound `State`
S_state = t.TypeVar("S_state")
U_contra = t.TypeVar("U_contra", contravariant=True)
V_contra = t.TypeVar("V_contra", contravariant=True)


class BaseStateMachineContext(t.Generic[S_state, U_contra, V_contra], Context[S_state]):
    def __init__(
        self,
        state: S_state,
        fallback: t.Optional[t.Callable[[Exception], t.Optional[S_state]]] = None,
    ) -> None:
        self.__state = state
        self.__next_state: t.Optional[S_state] = None
        self._fallback = fallback

        self._initial = True
        self._entered = False
        self._aborted = False

    @override
    def set_state(self, state: S_state, final: bool = False) -> None:
        self.__next_state = state
        self._aborted = final

    @override
    def abort(self) -> None:
        self._aborted = True

    @property
    def state(self) -> S_state:
        return self.__state

    @property
    def next_state(self) -> t.Optional[S_state]:
        return self.__next_state

    @property
    def is_going_to_transit(self) -> bool:
        return self.__next_state is not None and self.__state is not self.__next_state

    @property
    def is_initial_state(self) -> bool:
        return self._initial

    @property
    def is_aborted(self) -> bool:
        return self._aborted

    def _check_aborted(self, income: U_contra) -> None:
        if self._aborted:
            raise AbortedStateReachedError(self.__state, income)

    def _reset_state(self, next_state: t.Optional[S_state] = None) -> t.Optional[tuple[S_state, S_state]]:
        if next_state is not None:
            self.__next_state = next_state

        if self.__next_state is None:
            return None

        source, self.__state, self.__next_state, self._entered = self.__state, self.__next_state, None, False

        return source, self.__state


class StateMachineExecutor(
    t.Generic[S_state, U_contra, V_contra],
    BaseStateMachineContext[S_state, U_contra, V_contra],
):
    def __init__(
        self,
        state: S_state,
        fallback: t.Optional[t.Callable[[Exception], t.Optional[S_state]]] = None,
        subscriber: t.Optional[StateMachineSubscriber[S_state, U_contra, V_contra]] = None,
    ) -> None:
        super().__init__(state, fallback)
        self.__subscriber = subscriber

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
        self._check_aborted(income)

        if self._initial:
            if self.__subscriber is not None:
                self.__subscriber.notify_initial(self.state)

            self._initial = False

        if not self._entered:
            if self.__subscriber is not None:
                self.__subscriber.notify_state_entered(self.state, income)

            self._entered = True

        return self

    def handle_outcome(self, income: U_contra, outcome: V_contra) -> None:
        if self.__subscriber is not None:
            self.__subscriber.notify_state_outcome(self.state, income, outcome)

    def leave_state(self, income: U_contra) -> None:
        if self.is_going_to_transit and self.__subscriber is not None:
            self.__subscriber.notify_state_left(self.state, income)

        self.reset_state()

        if self.is_aborted and self.__subscriber is not None:
            self.__subscriber.notify_final(self.state)

    def handle_state_error(self, err: Exception) -> bool:
        if self.__subscriber is not None:
            self.__subscriber.notify_state_failed(self.state, err)

        if self._fallback is None:
            return False

        return self.reset_state(self._fallback(err))

    def reset_state(self, next_state: t.Optional[S_state] = None) -> bool:
        transition = self._reset_state(next_state)

        if transition is not None and self.__subscriber is not None:
            self.__subscriber.notify_transition(*transition)

        return transition is not None


class AsyncStateMachineExecutor(
    t.Generic[S_state, U_contra, V_contra],
    BaseStateMachineContext[S_state, U_contra, V_contra],
):
    def __init__(
        self,
        state: S_state,
        fallback: t.Optional[t.Callable[[Exception], t.Optional[S_state]]] = None,
        subscriber: t.Optional[AsyncStateMachineSubscriber[S_state, U_contra, V_contra]] = None,
    ) -> None:
        super().__init__(state, fallback)
        self.__subscriber = subscriber

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
        self._check_aborted(income)

        if self._initial:
            if self.__subscriber is not None:
                await self.__subscriber.notify_initial(self.state)

            self._initial = False

        if not self._entered:
            if self.__subscriber is not None:
                await self.__subscriber.notify_state_entered(self.state, income)

            self._entered = True

        return self

    async def handle_outcome(self, income: U_contra, outcome: V_contra) -> None:
        if self.__subscriber is not None:
            await self.__subscriber.notify_state_outcome(self.state, income, outcome)

    async def leave_state(self, income: U_contra) -> None:
        if self.is_going_to_transit and self.__subscriber is not None:
            await self.__subscriber.notify_state_left(self.state, income)

        await self.reset_state()

        if self.is_aborted and self.__subscriber is not None:
            await self.__subscriber.notify_final(self.state)

    async def handle_state_error(self, err: Exception) -> bool:
        if self.__subscriber is not None:
            await self.__subscriber.notify_state_failed(self.state, err)

        if self._fallback is None:
            return False

        return await self.reset_state(self._fallback(err))

    async def reset_state(self, next_state: t.Optional[S_state] = None) -> bool:
        transition = self._reset_state(next_state)

        if transition is not None and self.__subscriber is not None:
            await self.__subscriber.notify_transition(*transition)

        return transition is not None
