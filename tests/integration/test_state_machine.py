import typing as t

import pytest

from tests.stub.order_control_machine import (
    OrderControlStateMachine,
    OrderEvent,
    OrderItemAdded,
    OrderPaymentReceived,
    OrderProcessed,
    OrderShipped,
)
from tests.stub.traffic_light_machine import (
    AsyncTrafficStateMachine,
    CycleEvent,
    GoEvent,
    TrafficEvent,
    TrafficStateMachine,
)


@pytest.mark.parametrize(
    ("incomes", "outcomes"),
    [
        pytest.param(
            [
                OrderItemAdded(3),
                OrderItemAdded(7),
                OrderPaymentReceived(4),
                OrderProcessed(),
                OrderPaymentReceived(6),
                OrderProcessed(),
                OrderItemAdded(1),
                OrderShipped(),
            ],
            [
                "item added to order",
                "item added to order",
                "payment received",
                "can't handle command OrderProcessed() while waiting for payment",
                "payment received, processing the order",
                "the order was processed",
                "can't handle command OrderItemAdded(amount=1) while shipping the order",
                "the order was shipped",
            ],
        ),
    ],
)
def test_order_control_machine_returns_expected_outcomes(
    order_control_machine: OrderControlStateMachine,
    incomes: t.Sequence[OrderEvent],
    outcomes: t.Sequence[str],
) -> None:
    assert list(order_control_machine.run(incomes)) == list(outcomes)


@pytest.mark.parametrize(
    ("incomes", "outcomes"),
    [
        pytest.param(
            [
                GoEvent(),
                CycleEvent(),
            ]
            * 4,
            [
                "you can go",
                "switched to yellow",
                "you may go on your own risk",
                "switched to red",
                "you can't go!",
                "switched to green",
                "you can go",
                "switched to yellow",
            ],
        ),
    ],
)
def test_traffic_light_machine_returns_expected_outcomes(
    traffic_light_machine: TrafficStateMachine,
    incomes: t.Sequence[TrafficEvent],
    outcomes: t.Sequence[str],
) -> None:
    assert [traffic_light_machine.run(income) for income in incomes] == list(outcomes)


@pytest.mark.parametrize(
    ("incomes", "outcomes"),
    [
        pytest.param(
            [
                GoEvent(),
                CycleEvent(),
            ]
            * 4,
            [
                "you can go",
                "switched to yellow",
                "you may go on your own risk",
                "switched to red",
                "you can't go!",
                "switched to green",
                "you can go",
                "switched to yellow",
            ],
        ),
    ],
)
async def test_traffic_light_machine_async_returns_expected_outcomes(
    traffic_light_machine_async: AsyncTrafficStateMachine,
    incomes: t.Sequence[TrafficEvent],
    outcomes: t.Sequence[str],
) -> None:
    assert [await traffic_light_machine_async.run(income) for income in incomes] == list(outcomes)
