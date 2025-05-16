import typing as t

import pytest

from statomata.abc import StateMachineAsyncSubscriber, StateMachineSubscriber
from statomata.sdk import create_async_unary_sm, create_iterable_opt_sm, create_unary_sm
from tests.stub.order_control_machine import OrderControlStateMachine, WaitingForPayment
from tests.stub.traffic_light_machine import (
    AsyncGreen,
    AsyncTrafficState,
    AsyncTrafficStateMachine,
    Green,
    TrafficEvent,
    TrafficState,
    TrafficStateMachine,
)


@pytest.fixture
def traffic_light_subscribers() -> t.Sequence[StateMachineSubscriber[TrafficState, TrafficEvent, str]]:
    return []


@pytest.fixture
def traffic_light_machine(
    traffic_light_subscribers: t.Sequence[StateMachineSubscriber[TrafficState, TrafficEvent, str]],
) -> TrafficStateMachine:
    return create_unary_sm(Green(), subscribers=traffic_light_subscribers)


@pytest.fixture
def traffic_light_subscribers_async() -> t.Sequence[StateMachineAsyncSubscriber[AsyncTrafficState, TrafficEvent, str]]:
    return []


@pytest.fixture
def traffic_light_machine_async(
    traffic_light_subscribers_async: t.Sequence[StateMachineAsyncSubscriber[AsyncTrafficState, TrafficEvent, str]],
) -> AsyncTrafficStateMachine:
    return create_async_unary_sm(AsyncGreen(), subscribers=traffic_light_subscribers_async)


@pytest.fixture
def order_control_machine() -> OrderControlStateMachine:
    return create_iterable_opt_sm(WaitingForPayment())
