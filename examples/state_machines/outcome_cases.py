import typing as t

from statomata.declarative import DeclarativeStateMachine, State


class OutcomeCases(DeclarativeStateMachine):
    idle = State(initial=True)
    unary, unary_async, iterable, iterable_async = State(), State(), State(), State()

    @idle.to(unary)
    def invoke_unary(self, n: int) -> int:
        return n + 1

    # @idle.to(unary_async)
    # async def invoke_unary_async(self, n: int) -> int:
    #     await asyncio.sleep(0.0)
    #     return n + 1

    @idle.to(iterable)
    def invoke_iterable(self, n: int) -> t.Iterable[int]:
        for i in range(n):
            yield i + 1

    # @idle.to(iterable_async)
    # async def invoke_iterable_async(self, n: int) -> t.AsyncIterable[int]:
    #     for i in range(n):
    #         await asyncio.sleep(0.0)
    #         yield i + 1
