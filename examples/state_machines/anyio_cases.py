import typing as t
from dataclasses import dataclass

from typing_extensions import assert_never, override

from statomata.abc import Context
from statomata.iterable import AsyncIterableState


@dataclass(frozen=True)
class ProcessMessage:
    value: int


@dataclass(frozen=True)
class StopMessage:
    pass


StreamMessage = t.Union[ProcessMessage, StopMessage]


class ProcessingState(AsyncIterableState[StreamMessage, str]):
    @override
    async def handle(
        self,
        income: StreamMessage,
        context: Context[AsyncIterableState[StreamMessage, str]],
    ) -> t.AsyncIterator[str]:
        if isinstance(income, ProcessMessage):
            yield f"Processing: {income.value}"
            if income.value > 10:
                yield "Large value detected"
            elif income.value < 0:
                context.set_state(ErrorState())
                yield "Negative value, switching to error state"
        elif isinstance(income, StopMessage):
            context.abort()
            yield "Stopping processing"
        else:
            assert_never(income)


class ErrorState(AsyncIterableState[StreamMessage, str]):
    @override
    async def handle(
        self,
        income: StreamMessage,
        context: Context[AsyncIterableState[StreamMessage, str]],
    ) -> t.AsyncIterator[str]:
        if isinstance(income, ProcessMessage):
            yield f"Error: Cannot process {income.value} in error state"
        elif isinstance(income, StopMessage):
            context.abort()
            yield "Stopping in error state"
        else:
            assert_never(income)
