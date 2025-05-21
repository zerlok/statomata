import typing as t

import pytest

from examples.state_machines.outcome_cases import AsyncOutcomeCases, OutcomeCases


class TestSyncOutcome:
    @pytest.fixture
    def sm(self) -> OutcomeCases:
        return OutcomeCases()

    @pytest.mark.parametrize(("income", "outcome"), [pytest.param(42, 43)])
    def test_unary_outcome(self, sm: OutcomeCases, income: int, outcome: int) -> None:
        assert sm.invoke_unary(income) == outcome

    @pytest.mark.parametrize(("income", "outcome"), [pytest.param(3, [1, 2, 3])])
    def test_iterable_outcome(self, sm: OutcomeCases, income: int, outcome: t.Sequence[int]) -> None:
        assert list(sm.invoke_iterable(income)) == outcome


class TestAsyncOutcome:
    @pytest.fixture
    def sm(self) -> AsyncOutcomeCases:
        return AsyncOutcomeCases()

    @pytest.mark.parametrize(("income", "outcome"), [pytest.param(42, 43)])
    async def test_unary_outcome(self, sm: AsyncOutcomeCases, income: int, outcome: int) -> None:
        assert await sm.invoke_unary(income) == outcome

    @pytest.mark.parametrize(("income", "outcome"), [pytest.param(3, [1, 2, 3])])
    async def test_iterable_outcome(self, sm: AsyncOutcomeCases, income: int, outcome: t.Sequence[int]) -> None:
        assert [i async for i in sm.invoke_iterable(income)] == outcome
