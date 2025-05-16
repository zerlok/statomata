from __future__ import annotations

import asyncio
import typing as t

from typing_extensions import override

from statomata.abc import StateMachine
from statomata.iterable import AsyncIterableState

if t.TYPE_CHECKING:
    from anyio.abc import ObjectReceiveStream, ObjectSendStream

    from statomata.executor import AsyncStateMachineExecutor

U_contra = t.TypeVar("U_contra", contravariant=True)
V_co = t.TypeVar("V_co", covariant=True)


class AnyioStreamStateMachine(t.Generic[U_contra, V_co], StateMachine[AsyncIterableState[U_contra, V_co]]):
    def __init__(
        self,
        executor: AsyncStateMachineExecutor[AsyncIterableState[U_contra, V_co], U_contra, V_co],
    ) -> None:
        self.__executor = executor

        self.__lock = asyncio.Lock()

    @property
    @override
    def current_state(self) -> AsyncIterableState[U_contra, V_co]:
        return self.__executor.state

    async def run(self, receiver: ObjectReceiveStream[U_contra], sender: ObjectSendStream[V_co]) -> None:
        async with self.__lock:
            async for income in receiver:
                async with self.__executor.visit_state(income) as context:
                    async for outcome in self.current_state.handle(income, context):
                        await sender.send(outcome)
                        await self.__executor.handle_outcome(income, outcome)

                if self.__executor.is_aborted:
                    break
