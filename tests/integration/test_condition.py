import pytest

from examples.state_machines.condition_cases import ConditionCases
from statomata.declarative import State


@pytest.mark.parametrize(
    ("value", "state"),
    [
        pytest.param(0, ConditionCases.idle),
        pytest.param(1, ConditionCases.idle),
        pytest.param(2, ConditionCases.idle),
        pytest.param(4, ConditionCases.idle),
        pytest.param(5, ConditionCases.idle),
        pytest.param(7, ConditionCases.ok),
    ],
)
def test_all_condition_evaluated_as_expected(sm: ConditionCases, state: State) -> None:
    sm.evaluate_all_123()
    assert sm.current_state is state


@pytest.mark.parametrize(
    ("value", "state"),
    [
        pytest.param(0, ConditionCases.idle),
        pytest.param(1, ConditionCases.ok),
        pytest.param(2, ConditionCases.ok),
        pytest.param(4, ConditionCases.idle),
        pytest.param(5, ConditionCases.ok),
        pytest.param(7, ConditionCases.ok),
    ],
)
def test_any_condition_evaluated_as_expected(sm: ConditionCases, state: State) -> None:
    sm.evaluate_any_012()
    assert sm.current_state is state


@pytest.fixture
def value() -> int:
    raise NotImplementedError


@pytest.fixture
def sm(value: int) -> ConditionCases:
    return ConditionCases(value)
