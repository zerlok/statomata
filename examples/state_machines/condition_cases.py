from statomata.declarative import DeclarativeStateMachine, State


class ConditionCases(DeclarativeStateMachine):
    idle = State(initial=True)
    ok, not_ok = State(), State()

    def __init__(self, value: int) -> None:
        super().__init__()
        self.__value = value

    @property
    def val0(self) -> bool:
        return bool(self.__value & 0)

    @property
    def val1(self) -> bool:
        return bool(self.__value & 1)

    @property
    def val2(self) -> bool:
        return bool(self.__value & 2)

    @property
    def val3(self) -> bool:
        return bool(self.__value & 3)

    @property
    def val4(self) -> bool:
        return bool(self.__value & 4)

    @idle.to(ok).when(val0) | val1 | val2
    def evaluate_any_012(self) -> None:
        pass

    @idle.to(ok).when(val1) & val2 & val3
    def evaluate_all_123(self) -> None:
        pass
