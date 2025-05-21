import typing as t

import pytest

from examples.state_machines.outcome_cases import OutcomeCases


@pytest.fixture
def sm() -> OutcomeCases:
    return OutcomeCases()


@pytest.mark.parametrize(("income", "outcome"), [pytest.param(42, 43)])
def test_unary_outcome(sm: OutcomeCases, income: int, outcome: int) -> None:
    assert sm.invoke_unary(income) == outcome


# @pytest.mark.parametrize(("income", "outcome"), [pytest.param(42, 43)])
# async def test_unary_async_outcome(sm: OutcomeCases, income: int, outcome: int) -> None:
#     assert await sm.invoke_unary_async(income) == outcome


@pytest.mark.parametrize(("income", "outcome"), [pytest.param(3, [1, 2, 3])])
def test_iterable_outcome(sm: OutcomeCases, income: int, outcome: t.Sequence[int]) -> None:
    assert list(sm.invoke_iterable(income)) == outcome


# @pytest.mark.parametrize(("income", "outcome"), [pytest.param(3, [1, 2, 3])])
# async def test_iterable_async_outcome(sm: OutcomeCases, income: int, outcome: t.Sequence[int]) -> None:
#     assert [i async for i in sm.invoke_iterable_async(income)] == outcome
