import asyncio
import typing as t

from statomata.declarative import DeclarativeStateMachine, State
from statomata.declarative.state_machine import AsyncDeclarativeStateMachine


class OutcomeCases(DeclarativeStateMachine):
    idle = State(initial=True)
    unary, iterable = State(), State()

    @idle.to(unary)
    def invoke_unary(self, n: int) -> int:
        return n + 1

    @idle.to(iterable)
    def invoke_iterable(self, n: int) -> t.Iterable[int]:
        for i in range(n):
            yield i + 1


class AsyncOutcomeCases(AsyncDeclarativeStateMachine):
    idle = State(initial=True)
    unary, iterable = State(), State()

    # NOTE: it is `Callable[[AsyncOutcomeCases, int], Coroutine[Any, Any, int]]`
    @idle.to(unary)
    async def invoke_unary(self, n: int) -> int:  # type: ignore[misc]
        await asyncio.sleep(0.0)
        return n + 1

    @idle.to(iterable)
    async def invoke_iterable(self, n: int) -> t.AsyncIterable[int]:
        for i in range(n):
            await asyncio.sleep(0.0)
            yield i + 1
