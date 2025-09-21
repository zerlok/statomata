import typing as t

import pytest

from examples.state_machines.defer_recall_cases import AuthInput, AuthMachine


@pytest.mark.parametrize(
    ("incomes", "outcomes"),
    [
        pytest.param(
            [{"username": "John"}, {"password": "secret"}, {"data": "ok"}],
            [
                "Username 'John' accepted.",
                "User 'John' authenticated.",
                "Welcome John, processing data: ok",
            ],
            id="3 incomes normal order",
        ),
        pytest.param(
            [{"data": "ok"}, {"password": "secret"}, {"username": "John"}],
            [
                "Username is missing.",
                "Username is missing.",
                "Welcome John, processing data: ok",
            ],
            id="3 incomes inverted",
        ),
        pytest.param(
            [{"password": "secret", "username": "John", "data": "ok"}],
            ["Welcome John, processing data: ok"],
            id="one income",
        ),
    ],
)
def test_order_control_machine_returns_expected_outcomes(
    auth_machine: AuthMachine,
    incomes: t.Sequence[AuthInput],
    outcomes: t.Sequence[str],
) -> None:
    assert [auth_machine.run(income) for income in incomes] == list(outcomes)
