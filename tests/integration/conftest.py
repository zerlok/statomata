import typing as t

import pytest

from examples.state_machines.defer_recall_cases import AuthMachine, create_auth_machine
from examples.state_machines.order_control_low_level import OrderControlStateMachine, WaitingForPayment
from examples.state_machines.traffic_light_low_level import (
    AsyncGreen,
    AsyncTrafficState,
    AsyncTrafficStateMachine,
    Green,
    TrafficEvent,
    TrafficState,
    TrafficStateMachine,
)
from statomata.abc import AsyncStateMachineSubscriber, StateMachineSubscriber
from statomata.sdk import create_async_unary_sm, create_iterable_opt_sm, create_unary_sm


@pytest.fixture
def traffic_light_subscribers() -> t.Sequence[StateMachineSubscriber[TrafficState, TrafficEvent, str]]:
    return []


@pytest.fixture
def traffic_light_machine(
    traffic_light_subscribers: t.Sequence[StateMachineSubscriber[TrafficState, TrafficEvent, str]],
) -> TrafficStateMachine:
    return create_unary_sm(Green(), subscribers=traffic_light_subscribers)


@pytest.fixture
def traffic_light_subscribers_async() -> t.Sequence[AsyncStateMachineSubscriber[AsyncTrafficState, TrafficEvent, str]]:
    return []


@pytest.fixture
def traffic_light_machine_async(
    traffic_light_subscribers_async: t.Sequence[AsyncStateMachineSubscriber[AsyncTrafficState, TrafficEvent, str]],
) -> AsyncTrafficStateMachine:
    return create_async_unary_sm(AsyncGreen(), subscribers=traffic_light_subscribers_async)


@pytest.fixture
def order_control_machine() -> OrderControlStateMachine:
    return create_iterable_opt_sm(WaitingForPayment())


@pytest.fixture
def auth_machine() -> AuthMachine:
    return create_auth_machine()
