import typing as t

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
    def set_finished(self, reason: str, *details: object) -> None:
        # NOTE: final state won't handle income and never returns.
        final_state = t.cast(S_state, FinalState(reason, *details))
        self.set_state(final_state)

    @property
    def state(self) -> S_state:
        return self.__state

    @property
    def is_started(self) -> bool:
        return self.__started

    @property
    def is_finished(self) -> bool:
        return self.__finished

    def start_state(self, income: U_contra) -> Context[S_state]:
        if not self.__started:
            self.__started = True
            if self.__subscriber is not None:
                self.__subscriber.notify_start(self.__state)

        if self.__subscriber is not None:
            self.__subscriber.notify_state_start(self.__state, income)

        return self

    def handle_outcome(self, income: U_contra, outcome: V_contra) -> None:
        if self.__subscriber is not None:
            self.__subscriber.notify_state_outcome(self.__state, income, outcome)

    def finish_state(self, income: U_contra) -> None:
        if self.__subscriber is not None:
            self.__subscriber.notify_state_finish(self.__state, income)

        self.reset_state()

        if isinstance(self.__state, FinalState):
            self.__finished = True
            if self.__subscriber is not None:
                # FIXME: possible bug, not sure if final state is a subtype of S_state
                self.__subscriber.notify_finish(t.cast(S_state, self.__state))

    def handle_state_error(self, err: Exception) -> bool:
        self.__next_state = None

        if self.__subscriber is not None:
            self.__subscriber.notify_state_error(self.__state, err)

        if self.__fallback is None:
            return False

        self.__next_state = self.__fallback(err)

        return self.reset_state()

    def reset_state(self) -> bool:
        if self.__next_state is None:
            return False

        source, self.__state, self.__next_state = self.__state, self.__next_state, None

        if self.__subscriber is not None:
            self.__subscriber.notify_transition(source, self.__state)

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
    def set_finished(self, reason: str, *details: object) -> None:
        # NOTE: final state won't handle income and never returns.
        final_state = t.cast(S_state, FinalState(reason, *details))
        self.set_state(final_state)

    @property
    def state(self) -> S_state:
        return self.__state

    @property
    def is_started(self) -> bool:
        return self.__started

    @property
    def is_finished(self) -> bool:
        return self.__finished

    async def start_state(self, income: U_contra) -> Context[S_state]:
        if not self.__started:
            self.__started = True
            if self.__subscriber is not None:
                await self.__subscriber.notify_start(self.__state)

        if self.__subscriber is not None:
            await self.__subscriber.notify_state_start(self.__state, income)

        return self

    async def handle_outcome(self, income: U_contra, outcome: V_contra) -> None:
        if self.__subscriber is not None:
            await self.__subscriber.notify_state_outcome(self.__state, income, outcome)

    async def finish_state(self, income: U_contra) -> None:
        if self.__subscriber is not None:
            await self.__subscriber.notify_state_finish(self.__state, income)

        await self.reset_state()

        if isinstance(self.__state, FinalState):
            self.__finished = True
            if self.__subscriber is not None:
                # FIXME: possible bug, not sure if final state is a subtype of S_state
                await self.__subscriber.notify_finish(t.cast(S_state, self.__state))

    async def handle_state_error(self, err: Exception) -> bool:
        self.__next_state = None

        if self.__subscriber is not None:
            await self.__subscriber.notify_state_error(self.__state, err)

        if self.__fallback is None:
            return False

        self.__next_state = self.__fallback(err)

        return await self.reset_state()

    async def reset_state(self) -> bool:
        if self.__next_state is None:
            return False

        source, self.__state, self.__next_state = self.__state, self.__next_state, None

        if self.__subscriber is not None:
            await self.__subscriber.notify_transition(source, self.__state)

        return True
