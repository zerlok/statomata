import typing as t

from statomata.declarative.builder import State
from statomata.declarative.state_machine import DeclarativeStateMachine


class PositiveNumberStore(DeclarativeStateMachine):
    idle = State(initial=True)
    opened = State()
    broken = State(fallback=ValueError)
    closed = State(final=True)

    def __init__(self) -> None:
        super().__init__()
        self.__nums = list[int]()

    @property
    def values(self) -> t.Sequence[int]:
        return self.__nums

    @property
    def has_negative(self) -> bool:
        return any(n < 0 for n in self.__nums)

    @idle.to(opened).idempotent()
    def open(self) -> None:
        pass

    @broken.to(opened).idempotent()
    def recover(self) -> None:
        self.__nums = [n for n in self.__nums if n >= 0]

    @opened.to(closed)
    @broken.to(closed)
    @closed.idempotent().returns(values)
    def close(self) -> None:
        pass

    @opened.ternary(has_negative).then(broken).otherwise(opened)
    def extend(self, *nums: int) -> None:
        self.__nums.extend(nums)
