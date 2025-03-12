from __future__ import annotations

import asyncio
import typing as t

from anyio.abc import ObjectReceiveStream, ObjectSendStream
from typing_extensions import override

from statomata.abc import StateMachine

if t.TYPE_CHECKING:
    from statomata.executor import AsyncStateMachineExecutor
    from statomata.iterable import AsyncIterableState

U_co = t.TypeVar("U_co", covariant=True)
V_contra = t.TypeVar("V_contra", contravariant=True)


class AnyioStateMachine(
    t.Generic[V_contra, U_co],
    StateMachine[tuple[ObjectSendStream[V_contra], ObjectReceiveStream[U_co]], t.Awaitable[None]],
):
    def __init__(
        self,
        executor: AsyncStateMachineExecutor[AsyncIterableState[U_co, V_contra], U_co, V_contra],
    ) -> None:
        self.__executor = executor

        self.__lock = asyncio.Lock()

    @property
    def current_state(self) -> AsyncIterableState[U_co, V_contra]:
        return self.__executor.state

    @override
    async def run(self, input_: tuple[ObjectSendStream[V_contra], ObjectReceiveStream[U_co]]) -> None:
        sender, receiver = input_
        async with sender, receiver:
            await self.process(sender, receiver)

    async def process(self, sender: ObjectSendStream[V_contra], receiver: ObjectReceiveStream[U_co]) -> None:
        async with self.__lock:
            async for income in receiver:
                context = await self.__executor.start_state(income)
                try:
                    async for outcome in self.current_state.handle(income, context):
                        await sender.send(outcome)
                        await self.__executor.handle_outcome(income, outcome)

                except Exception as err:
                    ok = await self.__executor.handle_state_error(err)
                    if not ok:
                        raise

                else:
                    await self.__executor.finish_state(income)

                if self.__executor.is_finished:
                    return
