import asyncio
import typing as t

from typing_extensions import override

from statomata.abc import Context
from statomata.iterable import AsyncIterableState
from statomata.sdk import create_async_iterable_sm


class StrPublishState(AsyncIterableState[str, str]):
    def __init__(self, value: str) -> None:
        self.__value = value

    @override
    async def handle(
        self,
        income: str,
        context: Context[AsyncIterableState[str, str]],
    ) -> t.AsyncIterable[str]:
        if income.isalpha():
            context.set_state(StrPublishState(income))
            return

        elif income.isnumeric():
            self.__value *= int(income)

        else:
            yield self.__value


async def main() -> None:
    sm = create_async_iterable_sm(StrPublishState("a"))

    async def commands() -> t.AsyncIterable[str]:
        for i in ["", "", "b", "", "5", ""]:
            await asyncio.sleep(0.1)
            yield i

    async for out in sm.run(commands()):
        print(out)


if __name__ == "__main__":
    asyncio.run(main())
